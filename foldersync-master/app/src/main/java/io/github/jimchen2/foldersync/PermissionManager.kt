package io.github.jimchen2.foldersync

import android.Manifest
import android.app.Activity
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.net.Uri
import android.os.Build
import android.provider.Settings
import androidx.core.app.ActivityCompat
import androidx.core.content.ContextCompat

class PermissionManager(private val context: Context) {

    companion object {
        const val BACKGROUND_LOCATION_PERMISSION_REQUEST_CODE = 124
    }

    fun checkAndRequestPermissions(activity: Activity) {
        // Internet permission is declared in AndroidManifest.xml and doesn't need runtime request

        // For Android 11 and above, we use the Storage Access Framework
        // This doesn't require a runtime permission, but we need to request folder access
        // This is typically done using ACTION_OPEN_DOCUMENT_TREE intent in MainActivity

        // Check for background location permission (as a proxy for background processing)
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
            if (ContextCompat.checkSelfPermission(
                    context,
                    Manifest.permission.ACCESS_BACKGROUND_LOCATION
                ) != PackageManager.PERMISSION_GRANTED
            ) {
                requestBackgroundPermission(activity)
            }
        }
    }

    fun requestBackgroundPermission(activity: Activity) {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
            ActivityCompat.requestPermissions(
                activity,
                arrayOf(Manifest.permission.ACCESS_BACKGROUND_LOCATION),
                BACKGROUND_LOCATION_PERMISSION_REQUEST_CODE
            )
        }
    }

    fun openAppSettings(activity: Activity) {
        val intent = Intent(Settings.ACTION_APPLICATION_DETAILS_SETTINGS)
        val uri = Uri.fromParts("package", context.packageName, null)
        intent.data = uri
        activity.startActivity(intent)
    }
}
