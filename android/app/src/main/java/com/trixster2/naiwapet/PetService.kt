package com.trixster2.naiwapet

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.app.Service
import android.content.Context
import android.content.Intent
import android.graphics.PixelFormat
import android.os.Build
import android.os.IBinder
import android.provider.Settings
import android.util.DisplayMetrics
import android.view.Gravity
import android.view.WindowManager

class PetService : Service() {

    private lateinit var wm: WindowManager
    private var view: PetView? = null

    override fun onBind(intent: Intent?): IBinder? = null

    override fun onCreate() {
        super.onCreate()
        wm = getSystemService(Context.WINDOW_SERVICE) as WindowManager
        channel()
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        when (intent?.action) {
            ACTION_QUIT -> {
                remove()
                stopSelf()
                return START_NOT_STICKY
            }
            ACTION_WALK -> view?.startWalking()
            ACTION_IDLE -> view?.stopWalking()
            else -> if (view == null) place()
        }
        return START_STICKY
    }

    private fun size(): Pair<Int, Int> =
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
            val b = wm.currentWindowMetrics.bounds
            b.width() to b.height()
        } else {
            val dm = DisplayMetrics()
            @Suppress("DEPRECATION")
            wm.defaultDisplay.getRealMetrics(dm)
            dm.widthPixels to dm.heightPixels
        }

    private fun place() {
        if (!Settings.canDrawOverlays(this)) {
            stopSelf()
            return
        }
        val (sw, sh) = size()
        val pet = PetView(this, resources.displayMetrics.density)
        val w = pet.artWidth + (28 * pet.resources.displayMetrics.density).toInt()
        val h = pet.artHeight + (28 * pet.resources.displayMetrics.density).toInt()

        val lp = WindowManager.LayoutParams(
            w, h,
            WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY,
            WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE or
                WindowManager.LayoutParams.FLAG_LAYOUT_NO_LIMITS,
            PixelFormat.TRANSLUCENT
        ).apply {
            gravity = Gravity.TOP or Gravity.START
            x = sw - w - (16 * pet.resources.displayMetrics.density).toInt()
            y = sh - h
        }

        var x = lp.x.toFloat()
        var y = lp.y.toFloat()
        val ground = (sh - h).toFloat()

        pet.onTranslate = { dx, dy ->
            val nx = (x + dx).coerceIn(0f, (sw - w).toFloat())
            val ny = (y + dy).coerceIn(0f, ground)
            if (nx == x && dx != 0f) pet.onEdgeBounce()
            if (nx != x || ny != y) {
                x = nx
                y = ny
                lp.x = x.toInt()
                lp.y = y.toInt()
                runCatching { wm.updateViewLayout(pet, lp) }
            }
        }

        startForeground(NOTIFICATION_ID, buildNotification())
        runCatching { wm.addView(pet, lp) }
            .onSuccess { view = pet }
            .onFailure { stopSelf() }
    }

    private fun remove() {
        view?.let { runCatching { wm.removeView(it) } }
        view = null
    }

    private fun channel() {
        val nm = getSystemService(NotificationManager::class.java)
        nm.createNotificationChannel(
            NotificationChannel(
                CHANNEL_ID, getString(R.string.app_name), NotificationManager.IMPORTANCE_LOW
            )
        )
    }

    private fun buildNotification(): Notification {
        val open = PendingIntent.getActivity(
            this, 0, Intent(this, MainActivity::class.java),
            PendingIntent.FLAG_IMMUTABLE
        )
        return Notification.Builder(this, CHANNEL_ID)
            .setSmallIcon(R.drawable.ic_stat_pet)
            .setContentTitle(getString(R.string.notif_title))
            .setContentText(getString(R.string.notif_text))
            .setContentIntent(open)
            .setOngoing(true)
            .build()
    }

    override fun onDestroy() {
        remove()
        super.onDestroy()
    }

    companion object {
        const val ACTION_WALK = "com.trixster2.naiwapet.WALK"
        const val ACTION_IDLE = "com.trixster2.naiwapet.IDLE"
        const val ACTION_QUIT = "com.trixster2.naiwapet.QUIT"
        private const val CHANNEL_ID = "pet"
        private const val NOTIFICATION_ID = 1
    }
}
