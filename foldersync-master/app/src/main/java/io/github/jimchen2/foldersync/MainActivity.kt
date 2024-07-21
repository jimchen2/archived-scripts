package io.github.jimchen2.foldersync

import android.app.Activity
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Bundle
import android.widget.Button
import android.widget.EditText
import android.widget.TextView
import android.widget.Toast
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AppCompatActivity
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.GlobalScope
import kotlinx.coroutines.launch

class MainActivity : AppCompatActivity() {
    private lateinit var credManager: CredentialsManager
    private lateinit var s3Manager: S3SyncManager
    private lateinit var permissionManager: PermissionManager
    private var selectedFolderUri: android.net.Uri? = null

    private val folderPicker = registerForActivityResult(ActivityResultContracts.StartActivityForResult()) { result ->
        if (result.resultCode == Activity.RESULT_OK) {
            result.data?.data?.let { uri ->
                selectedFolderUri = uri
                findViewById<TextView>(R.id.selectedFolderText).text = "Selected: ${uri.path}"
            }
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        credManager = CredentialsManager(this)
        s3Manager = S3SyncManager()
        permissionManager = PermissionManager(this)

        loadCredentials()
        setupListeners()
        permissionManager.checkAndRequestPermissions(this)
    }

    private fun loadCredentials() {
        val cred = credManager.loadCredentials()
        findViewById<EditText>(R.id.accessKeyInput).setText(cred.accessKey)
        findViewById<EditText>(R.id.secretKeyInput).setText(cred.secretKey)
        findViewById<EditText>(R.id.regionInput).setText(cred.region)
        findViewById<EditText>(R.id.bucketInput).setText(cred.bucket)
        findViewById<EditText>(R.id.pathInput).setText(cred.path)
    }

    private fun setupListeners() {
        findViewById<Button>(R.id.selectFolderButton).setOnClickListener {
            folderPicker.launch(Intent(Intent.ACTION_OPEN_DOCUMENT_TREE))
        }

        findViewById<Button>(R.id.syncButton).setOnClickListener {
            if (selectedFolderUri != null) syncWithS3() else Toast.makeText(this, "Select a folder first", Toast.LENGTH_SHORT).show()
        }
    }

    private fun syncWithS3() {
        val cred = CredentialsManager.Credentials(
            findViewById<EditText>(R.id.accessKeyInput).text.toString(),
            findViewById<EditText>(R.id.secretKeyInput).text.toString(),
            findViewById<EditText>(R.id.regionInput).text.toString(),
            findViewById<EditText>(R.id.bucketInput).text.toString(),
            findViewById<EditText>(R.id.pathInput).text.toString()
        )
        credManager.saveCredentials(cred)

        GlobalScope.launch(Dispatchers.IO) {
            try {
                s3Manager.sync(cred, selectedFolderUri!!)
                launch(Dispatchers.Main) { Toast.makeText(this@MainActivity, "Sync completed", Toast.LENGTH_SHORT).show() }
            } catch (e: Exception) {
                launch(Dispatchers.Main) { Toast.makeText(this@MainActivity, "Sync failed: ${e.message}", Toast.LENGTH_SHORT).show() }
            }
        }
    }

    override fun onRequestPermissionsResult(requestCode: Int, permissions: Array<out String>, grantResults: IntArray) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults)
        when (requestCode) {
            PermissionManager.BACKGROUND_LOCATION_PERMISSION_REQUEST_CODE -> {
                if (grantResults.isNotEmpty() && grantResults[0] == PackageManager.PERMISSION_GRANTED) {
                    // Permission granted, proceed with your operation
                } else {
                    // Permission denied, show a message or open app settings
                    Toast.makeText(this, "Background location permission is required for background syncing", Toast.LENGTH_LONG).show()
                    permissionManager.openAppSettings(this)
                }
            }
        }
    }
}
