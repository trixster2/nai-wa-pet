package com.trixster2.naiwapet

import android.content.Context
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.graphics.Canvas
import android.graphics.Matrix
import android.os.SystemClock
import android.view.MotionEvent
import android.view.View
import kotlin.math.abs
import kotlin.math.max
import kotlin.math.min
import kotlin.math.sin

/**
 * Draws the plush and runs its motion. The formulas are a direct port of
 * pet.py's _transform() so the phone and the desktop behave identically.
 */
class PetView(
    context: Context,
    private val density: Float,
) : View(context) {

    /** Ask PetService to move the overlay window by this many pixels. */
    var onTranslate: ((Float, Float) -> Unit)? = null

    private val front: Bitmap
    private val blink: Bitmap
    private val side: Bitmap
    private val unit: Float

    private enum class Mode { IDLE, WALK, DRAG }

    private var mode = Mode.IDLE
    private var facing = 1
    private var t = 0f
    private var lastFrame = 0L
    private var react = 0f
    private var blinkLeft = 0f
    private var nextBlink = 2.5f
    private var idleLeft = 5f
    private var walkLeft = 0f
    private var dragTilt = 0f

    private var downX = 0f
    private var downY = 0f
    private var lastX = 0f
    private var lastY = 0f
    private var travel = 0f
    private val slop = 12f * density

    val artWidth: Int
    val artHeight: Int

    init {
        val target = (120 * density).toInt()
        fun load(id: Int): Bitmap {
            val raw = BitmapFactory.decodeResource(resources, id)
            val ratio = target.toFloat() / raw.height
            return Bitmap.createScaledBitmap(
                raw, max(1, (raw.width * ratio).toInt()), target, true
            )
        }
        front = load(R.drawable.idle)
        blink = load(R.drawable.blink)
        side = load(R.drawable.turn_b)
        artWidth = front.width
        artHeight = front.height
        unit = target.toFloat() / front.height
    }

    fun startWalking() {
        mode = Mode.WALK
        facing = if (Math.random() < 0.5) 1 else -1
        walkLeft = 3f + Math.random().toFloat() * 5f
    }

    fun stopWalking() {
        mode = Mode.IDLE
        idleLeft = 4f + Math.random().toFloat() * 8f
    }

    /** Called by the service when the window is clamped against a screen edge. */
    fun onEdgeBounce() {
        facing = -facing
    }

    private val ticker = object : Runnable {
        override fun run() {
            step()
            invalidate()
            postOnAnimation(this)
        }
    }

    override fun onAttachedToWindow() {
        super.onAttachedToWindow()
        lastFrame = SystemClock.uptimeMillis()
        postOnAnimation(ticker)
    }

    override fun onDetachedFromWindow() {
        removeCallbacks(ticker)
        super.onDetachedFromWindow()
    }

    private fun step() {
        val now = SystemClock.uptimeMillis()
        val dt = min(0.05f, (now - lastFrame) / 1000f)
        lastFrame = now
        t += dt

        if (blinkLeft > 0f) blinkLeft -= dt
        else if (t > nextBlink) {
            blinkLeft = 0.13f
            nextBlink = t + 2.4f + Math.random().toFloat() * 4.1f
        }
        if (react > 0f) react = max(0f, react - dt)

        when (mode) {
            Mode.WALK -> {
                onTranslate?.invoke(40f * density * facing * dt, 0f)
                walkLeft -= dt
                if (walkLeft <= 0f) stopWalking()
            }
            Mode.IDLE -> {
                idleLeft -= dt
                if (idleLeft <= 0f) startWalking()
            }
            Mode.DRAG -> dragTilt *= 0.86f
        }
    }

    private fun currentArt(): Bitmap = when {
        blinkLeft > 0f -> blink
        mode == Mode.WALK -> side
        else -> front
    }

    override fun onDraw(canvas: Canvas) {
        val art = currentArt()
        var sy = 1f + sin(t * 2.4f) * 0.014f
        var sx = 1f - sin(t * 2.4f) * 0.010f
        var deg = sin(t * 0.95f) * 1.8f
        var dy = 0f

        if (mode == Mode.WALK) {
            val w = t * 9.5f
            dy -= abs(sin(w)) * 4f * unit
            deg = sin(w) * 4.2f * facing
            sy *= 1f + sin(w * 2f) * 0.02f
        }
        if (mode == Mode.DRAG) {
            deg = dragTilt
            sy *= 1.04f
            sx *= 0.97f
        }
        if (react > 0f) {
            val k = react / 0.45f
            val wob = sin(k * Math.PI.toFloat() * 3f) * Math.pow(k.toDouble(), 0.6).toFloat()
            sy *= 1f - wob * 0.16f
            sx *= 1f + wob * 0.13f
            dy -= wob * 10f * unit
        }

        val m = Matrix()
        m.postTranslate(width / 2f, height - art.height / 2f - 6f * unit + dy)
        m.postRotate(deg)
        m.postScale(sx * facing, sy)
        m.postTranslate(-art.width / 2f, -art.height / 2f)
        canvas.drawBitmap(art, m, null)
    }

    override fun onTouchEvent(event: MotionEvent): Boolean {
        when (event.actionMasked) {
            MotionEvent.ACTION_DOWN -> {
                downX = event.rawX
                downY = event.rawY
                lastX = event.rawX
                lastY = event.rawY
                travel = 0f
                mode = Mode.DRAG
            }

            MotionEvent.ACTION_MOVE -> {
                val dx = event.rawX - lastX
                val dy = event.rawY - lastY
                lastX = event.rawX
                lastY = event.rawY
                travel = max(travel, abs(event.rawX - downX) + abs(event.rawY - downY))
                dragTilt = (dragTilt * 0.6f + dx * 0.9f).coerceIn(-13f, 13f)
                onTranslate?.invoke(dx, dy)
            }

            MotionEvent.ACTION_UP, MotionEvent.ACTION_CANCEL -> {
                if (travel < slop) react = 0.45f
                dragTilt = 0f
                stopWalking()
            }
        }
        return true
    }
}
