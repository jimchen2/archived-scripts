package io.github.jimchen2.foldersync

import android.net.Uri
import com.amazonaws.services.s3.model.S3ObjectSummary
import java.security.MessageDigest

class FileComparator {
    fun compareFiles(localFile: Uri, s3Object: S3ObjectSummary, localContent: ByteArray): Boolean {
        val localMd5 = calculateMd5(localContent)
        val s3Md5 = s3Object.eTag.replace("\"", "")
        return localMd5 == s3Md5
    }

    private fun calculateMd5(data: ByteArray): String {
        val md = MessageDigest.getInstance("MD5")
        val digest = md.digest(data)
        return digest.joinToString("") { "%02x".format(it) }
    }
}
