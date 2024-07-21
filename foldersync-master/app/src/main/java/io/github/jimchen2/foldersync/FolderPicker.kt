package io.github.jimchen2.foldersync

import android.content.Context
import android.net.Uri
import android.provider.DocumentsContract
import androidx.documentfile.provider.DocumentFile

class FolderPicker(private val context: Context) {
    fun listFiles(folderUri: Uri): List<DocumentFile> {
        val pickedDir = DocumentFile.fromTreeUri(context, folderUri) ?: return emptyList()
        return pickedDir.listFiles().toList()
    }

    fun getFileName(fileUri: Uri): String? {
        return DocumentsContract.getDocumentId(fileUri)?.substringAfterLast('/')
    }

    fun getFileContent(fileUri: Uri): ByteArray? {
        return context.contentResolver.openInputStream(fileUri)?.use { it.readBytes() }
    }
}
