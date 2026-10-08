package com.trixster2.naiwapet

import android.app.Activity
import android.content.Intent
import android.net.Uri
import android.os.Bundle
import android.provider.Settings
import android.view.Gravity
import android.widget.Button
import android.widget.LinearLayout
import android.widget.ScrollView
import android.widget.TextView

/**
 * Permission gate and controls. Built programmatically so the app stays a
 * handful of files.
 */
class MainActivity : Activity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        val pad = (20 * resources.displayMetrics.density).toInt()
        val column = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(pad, pad * 2, pad, pad)
        }

        column.addView(TextView(this).apply {
            text = getString(R.string.app_name)
            textSize = 26f
        })
        column.addView(TextView(this).apply {
            text = getString(R.string.intro)
            textSize = 15f
            setPadding(0, pad, 0, pad * 2)
        })

        val start = Button(this).apply { text = getString(R.string.btn_start) }
        val walk = Button(this).apply { text = getString(R.string.btn_walk) }
        val idle = Button(this).apply { text = getString(R.string.btn_idle) }
        val quit = Button(this).apply { text = getString(R.string.btn_quit) }
        for (b in listOf(start, walk, idle, quit)) column.addView(b)

        column.addView(TextView(this).apply {
            text = getString(R.string.origin_hint)
            textSize = 13f
            setPadding(0, pad * 2, 0, 0)
            gravity = Gravity.START
        })

        setContentView(ScrollView(this).apply { addView(column) })

        start.setOnClickListener {
            if (!Settings.canDrawOverlays(this)) {
                runCatching {
                    startActivity(
                        Intent(
                            Settings.ACTION_MANAGE_OVERLAY_PERMISSION,
                            Uri.parse("package:$packageName")
                        )
                    )
                }
                return@setOnClickListener
            }
            startService(Intent(this, PetService::class.java))
        }
        walk.setOnClickListener { send(PetService.ACTION_WALK) }
        idle.setOnClickListener { send(PetService.ACTION_IDLE) }
        quit.setOnClickListener { send(PetService.ACTION_QUIT) }
    }

    private fun send(action: String) {
        startService(Intent(this, PetService::class.java).setAction(action))
    }
}
