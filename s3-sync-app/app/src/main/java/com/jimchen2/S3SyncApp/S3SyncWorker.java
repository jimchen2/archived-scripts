package com.jimchen2.S3SyncApp;

import android.content.Context;
import android.content.SharedPreferences;
import android.net.Uri;
import android.util.Log;

import androidx.annotation.NonNull;
import androidx.documentfile.provider.DocumentFile;
import androidx.work.Worker;
import androidx.work.WorkerParameters;

import java.io.InputStream;
import java.net.URI;

import software.amazon.awssdk.auth.credentials.AwsBasicCredentials;
import software.amazon.awssdk.auth.credentials.StaticCredentialsProvider;
import software.amazon.awssdk.awscore.exception.AwsServiceException;
import software.amazon.awssdk.core.exception.SdkClientException;
import software.amazon.awssdk.core.sync.RequestBody;
import software.amazon.awssdk.regions.Region;
import software.amazon.awssdk.services.s3.S3Client;
import software.amazon.awssdk.services.s3.model.PutObjectRequest;
// Import UrlConnectionHttpClient
import software.amazon.awssdk.http.urlconnection.UrlConnectionHttpClient; // <--- ADD THIS IMPORT


public class S3SyncWorker extends Worker {

    private static final String TAG = "S3SyncWorker";
    public static final String WORK_TAG = "S3_SYNC_WORK";

    public S3SyncWorker(@NonNull Context context, @NonNull WorkerParameters workerParams) {
        super(context, workerParams);
    }

    @NonNull
    @Override
    public Result doWork() {
        Log.d(TAG, "S3SyncWorker: Work starting.");
        Context context = getApplicationContext();
        SharedPreferences prefs = context.getSharedPreferences(MainActivity.PREFS_NAME, Context.MODE_PRIVATE);

        String accessKey = prefs.getString(MainActivity.KEY_ACCESS_KEY, null);
        String secretKey = prefs.getString(MainActivity.KEY_SECRET_KEY, null);
        String endpoint = prefs.getString(MainActivity.KEY_ENDPOINT, null);
        String bucketName = prefs.getString(MainActivity.KEY_BUCKET_NAME, null);
        String bucketPath = prefs.getString(MainActivity.KEY_BUCKET_PATH, "");
        String localFolderUriStr = prefs.getString(MainActivity.KEY_LOCAL_FOLDER_URI, null);

        if (accessKey == null || secretKey == null || endpoint == null || bucketName == null || localFolderUriStr == null) {
            Log.e(TAG, "S3SyncWorker: Missing configuration for sync.");
            return Result.failure();
        }

        Uri localFolderUri = Uri.parse(localFolderUriStr);
        DocumentFile folder = DocumentFile.fromTreeUri(context, localFolderUri);

        if (folder == null || !folder.isDirectory()) {
            Log.e(TAG, "S3SyncWorker: Local folder not accessible or not a directory.");
            return Result.failure();
        }

        S3Client s3Client = null;

        try {
            Region region = Region.US_EAST_1; // Default region
            if (endpoint != null && !endpoint.isEmpty() && endpoint.contains("amazonaws.com")) {
                try {
                    String guessedRegion = null;
                    if (endpoint.equals("s3.amazonaws.com")) {
                        guessedRegion = "us-east-1";
                    } else {
                        String[] parts = endpoint.split("\\.");
                        // Try to match s3.region.amazonaws.com or s3-region.amazonaws.com patterns
                        if (parts.length >= 3 && parts[0].equals("s3") && !parts[1].equals("dualstack") && !parts[1].equals("amazonaws")) {
                            guessedRegion = parts[1]; // e.g., s3.us-west-2.amazonaws.com
                        } else if (parts.length >= 2 && parts[0].startsWith("s3-") && !parts[1].equals("amazonaws")) {
                            guessedRegion = parts[0].substring(3); // e.g., s3-us-west-1.amazonaws.com
                        } else if (parts.length >= 4 && parts[0].equals("s3") && parts[1].equals("dualstack")) {
                            guessedRegion = parts[2]; // e.g., s3.dualstack.us-east-1.amazonaws.com
                        }
                    }

                    if (guessedRegion != null) {
                        final String finalGuessedRegion = guessedRegion;
                        if (Region.regions().stream().anyMatch(r -> r.id().equals(finalGuessedRegion))) {
                            region = Region.of(finalGuessedRegion);
                            Log.i(TAG, "Parsed region from endpoint '" + endpoint + "': " + region.id());
                        } else {
                            Log.w(TAG, "Guessed region '" + finalGuessedRegion + "' is not a valid AWS region. Using default: " + region.id());
                        }
                    } else {
                        Log.w(TAG, "Could not parse region from AWS endpoint '" + endpoint + "'. Using default: " + region.id());
                    }
                } catch (Exception e) {
                    Log.w(TAG, "Error parsing region from AWS endpoint '" + endpoint + "', using default: " + region.id(), e);
                }
            } else {
                Log.i(TAG, "Non-AWS endpoint or custom endpoint provided. Using default region: " + region.id() + ". Ensure this is correct for your S3-compatible service.");
            }

            s3Client = S3Client.builder()
                    .region(region)
                    .endpointOverride(URI.create("https://" + endpoint)) // User provides endpoint without scheme
                    .credentialsProvider(StaticCredentialsProvider.create(AwsBasicCredentials.create(accessKey, secretKey)))
                    // Explicitly set the HttpClient to UrlConnectionHttpClient
                    .httpClientBuilder(UrlConnectionHttpClient.builder()) // <--- ADD THIS LINE
                    .build();

            Log.d(TAG, "S3 Client created for endpoint: " + endpoint + " and region: " + region.id() + " using UrlConnectionHttpClient.");

            int filesUploaded = 0;
            DocumentFile[] files = folder.listFiles();
            if (files != null) {
                for (DocumentFile file : files) {
                    if (file.isFile() && file.length() > 0) {
                        // User's original s3Key logic - seems correct
                        String s3Key = bucketPath + (bucketPath.endsWith("/") || bucketPath.isEmpty() ? "" : "/") + file.getName();

                        try (InputStream inputStream = context.getContentResolver().openInputStream(file.getUri())) {
                            if (inputStream == null) {
                                Log.w(TAG, "S3SyncWorker: Could not open input stream for " + file.getName());
                                continue;
                            }
                            PutObjectRequest putObjectRequest = PutObjectRequest.builder()
                                    .bucket(bucketName)
                                    .key(s3Key)
                                    .build();
                            s3Client.putObject(putObjectRequest, RequestBody.fromInputStream(inputStream, file.length()));
                            Log.i(TAG, "S3SyncWorker: Uploaded " + file.getName() + " to s3://" + bucketName + "/" + s3Key);
                            filesUploaded++;
                        } catch (Exception e) {
                            Log.e(TAG, "S3SyncWorker: Failed to upload " + file.getName() + " (key: " + s3Key + ")", e);
                            // Optionally, you might want to decide if one failed upload means the whole worker fails,
                            // or if it should continue with other files. Current logic continues.
                        }
                    } else if (file.isFile() && file.length() == 0) {
                        Log.w(TAG, "S3SyncWorker: Skipping empty file " + file.getName());
                    }
                }
            }
            Log.d(TAG, "S3SyncWorker: Sync complete. Files attempted (non-empty): " + (files != null ? java.util.Arrays.stream(files).filter(f -> f.isFile() && f.length() > 0).count() : 0) + ", Uploaded: " + filesUploaded);
            return Result.success();

        } catch (AwsServiceException | SdkClientException e) {
            Log.e(TAG, "S3SyncWorker: S3 Error during sync", e);
            return Result.failure();
        } catch (Exception e) { // Catch more general exceptions like IllegalArgumentException from URI.create if endpoint is malformed
            Log.e(TAG, "S3SyncWorker: General error during sync: " + e.getMessage(), e);
            return Result.failure();
        } finally {
            if (s3Client != null) {
                s3Client.close();
            }
            Log.d(TAG, "S3SyncWorker: Work finishing.");
        }
    }
}