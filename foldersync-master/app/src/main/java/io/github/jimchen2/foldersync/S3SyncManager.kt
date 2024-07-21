package io.github.jimchen2.foldersync

import android.content.Context
import android.net.Uri
import com.amazonaws.auth.BasicAWSCredentials
import com.amazonaws.regions.Regions
import com.amazonaws.services.s3.AmazonS3Client
import com.amazonaws.services.s3.model.ObjectMetadata
import com.amazonaws.services.s3.model.PutObjectRequest

class S3SyncManager(private val context: Context) {
    private lateinit var s3Client: AmazonS3Client
    private lateinit var folderPicker: FolderPicker
    private val fileComparator = FileComparator()

    fun sync(credentials: CredentialsManager.Credentials, localFolderUri: Uri) {
        val awsCredentials = BasicAWSCredentials(credentials.accessKey, credentials.secretKey)
        s3Client = AmazonS3Client(awsCredentials, Regions.fromName(credentials.region))
        folderPicker = FolderPicker(context)

        val localFiles = folderPicker.listFiles(localFolderUri)
        val s3Objects = s3Client.listObjects(credentials.bucket, credentials.path).objectSummaries

        for (localFile in localFiles) {
            val fileName = folderPicker.getFileName(localFile.uri) ?: continue
            val s3Key = "${credentials.path}/$fileName"
            val s3Object = s3Objects.find { it.key == s3Key }

            val localContent = folderPicker.getFileContent(localFile.uri) ?: continue

            if (s3Object == null || !fileComparator.compareFiles(localFile.uri, s3Object, localContent)) {
                uploadToS3(credentials.bucket, s3Key, localContent)
            }
        }
    }

    private fun uploadToS3(bucket: String, key: String, content: ByteArray) {
        val metadata = ObjectMetadata()
        metadata.contentLength = content.size.toLong()
        val putObjectRequest = PutObjectRequest(bucket, key, content.inputStream(), metadata)
        s3Client.putObject(putObjectRequest)
    }
}
