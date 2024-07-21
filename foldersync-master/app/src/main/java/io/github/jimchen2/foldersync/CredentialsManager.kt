package io.github.jimchen2.foldersync

import android.content.Context
import androidx.security.crypto.EncryptedSharedPreferences
import androidx.security.crypto.MasterKeys

class CredentialsManager(context: Context) {
    data class Credentials(
        val accessKey: String, val secretKey: String, val region: String,
        val bucket: String, val path: String
    )

    private val sharedPreferences = EncryptedSharedPreferences.create(
        "secure_prefs",
        MasterKeys.getOrCreate(MasterKeys.AES256_GCM_SPEC),
        context,
        EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV,
        EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM
    )

    fun loadCredentials() = Credentials(
        sharedPreferences.getString("access_key", "") ?: "",
        sharedPreferences.getString("secret_key", "") ?: "",
        sharedPreferences.getString("region", "") ?: "",
        sharedPreferences.getString("bucket", "") ?: "",
        sharedPreferences.getString("path", "") ?: ""
    )

    fun saveCredentials(credentials: Credentials) {
        with(sharedPreferences.edit()) {
            putString("access_key", credentials.accessKey)
            putString("secret_key", credentials.secretKey)
            putString("region", credentials.region)
            putString("bucket", credentials.bucket)
            putString("path", credentials.path)
            apply()
        }
    }
}
