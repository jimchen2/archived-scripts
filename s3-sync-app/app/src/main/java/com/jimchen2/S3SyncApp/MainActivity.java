package com.jimchen2.S3SyncApp;

import android.app.Activity;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.net.Uri;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.text.TextUtils;
import android.util.Log;
import android.view.View;
import android.widget.AdapterView;
import android.widget.ArrayAdapter;
import android.widget.Button;
import android.widget.Spinner;
import android.widget.TextView;
import android.widget.Toast;

import androidx.activity.result.ActivityResultLauncher;
import androidx.activity.result.contract.ActivityResultContracts;
import androidx.appcompat.app.AppCompatActivity;
import androidx.documentfile.provider.DocumentFile;
import androidx.work.Constraints;
import androidx.work.ExistingPeriodicWorkPolicy;
import androidx.work.NetworkType;
import androidx.work.OneTimeWorkRequest;
import androidx.work.PeriodicWorkRequest;
import androidx.work.WorkManager;

import com.google.android.material.textfield.TextInputEditText;

import java.util.concurrent.TimeUnit;


public class MainActivity extends AppCompatActivity {

    private static final String TAG = "MainActivity";
    public static final String PREFS_NAME = "S3SyncPrefs";
    public static final String KEY_ACCESS_KEY = "accessKey";
    public static final String KEY_SECRET_KEY = "secretKey";
    public static final String KEY_ENDPOINT = "endpoint";
    public static final String KEY_BUCKET_NAME = "bucketName";
    public static final String KEY_BUCKET_PATH = "bucketPath";
    public static final String KEY_LOCAL_FOLDER_URI = "localFolderUri";
    public static final String KEY_SCHEDULE_PREF = "schedulePref";

    // Schedule constants
    private static final int SCHEDULE_NEVER = 0;
    private static final int SCHEDULE_EVERY_12_HOURS = 1; // Changed from Daily
    private static final int SCHEDULE_EVERY_15_MINUTES_TEST = 2;

    private static final String[] SCHEDULE_OPTIONS = {
            "Never",
            "Every 12 Hours (Wi-Fi Only)", // Updated label
            "Every 15 Mins (Test, Any Network)" // Updated label
    };

    private TextInputEditText etAccessKey, etSecretKey, etEndpoint, etBucketName, etBucketPath;
    private Button btnSelectFolder, btnSyncNow;
    private TextView tvSelectedFolder, tvStatus;
    private Spinner spinnerSchedule;

    private Uri localFolderUri;
    private SharedPreferences sharedPreferences;
    private Handler mainThreadHandler;

    private ActivityResultLauncher<Intent> folderPickerLauncher;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        etAccessKey = findViewById(R.id.etAccessKey);
        etSecretKey = findViewById(R.id.etSecretKey);
        etEndpoint = findViewById(R.id.etEndpoint);
        etBucketName = findViewById(R.id.etBucketName);
        etBucketPath = findViewById(R.id.etBucketPath);
        btnSelectFolder = findViewById(R.id.btnSelectFolder);
        tvSelectedFolder = findViewById(R.id.tvSelectedFolder);
        spinnerSchedule = findViewById(R.id.spinnerSchedule);
        btnSyncNow = findViewById(R.id.btnSyncNow);
        tvStatus = findViewById(R.id.tvStatus);

        sharedPreferences = getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE);
        mainThreadHandler = new Handler(Looper.getMainLooper());

        loadPreferences();
        setupFolderPicker();
        setupSpinner();

        btnSelectFolder.setOnClickListener(v -> openFolderPicker());
        btnSyncNow.setOnClickListener(v -> {
            savePreferences();
            if (validateInputs()) {
                performSyncNow();
            }
        });
    }

    private void setupFolderPicker() {
        folderPickerLauncher = registerForActivityResult(
                new ActivityResultContracts.StartActivityForResult(),
                result -> {
                    if (result.getResultCode() == Activity.RESULT_OK && result.getData() != null) {
                        Uri treeUri = result.getData().getData();
                        if (treeUri != null) {
                            final int takeFlags = result.getData().getFlags()
                                    & (Intent.FLAG_GRANT_READ_URI_PERMISSION
                                    | Intent.FLAG_GRANT_WRITE_URI_PERMISSION);
                            try {
                                getContentResolver().takePersistableUriPermission(treeUri, takeFlags);
                                localFolderUri = treeUri;
                                tvSelectedFolder.setText("Selected: " + getPathFromUri(treeUri));
                                sharedPreferences.edit().putString(KEY_LOCAL_FOLDER_URI, localFolderUri.toString()).apply();
                            } catch (SecurityException e) {
                                Log.e(TAG, "Failed to take persistable URI permission", e);
                                Toast.makeText(this, "Could not get permanent access to folder.", Toast.LENGTH_SHORT).show();
                                localFolderUri = null;
                                tvSelectedFolder.setText("No folder selected or permission error.");
                                sharedPreferences.edit().remove(KEY_LOCAL_FOLDER_URI).apply();
                            }
                        }
                    }
                }
        );
    }

    private void openFolderPicker() {
        Intent intent = new Intent(Intent.ACTION_OPEN_DOCUMENT_TREE);
        folderPickerLauncher.launch(intent);
    }

    private String getPathFromUri(Uri treeUri) {
        DocumentFile documentFile = DocumentFile.fromTreeUri(this, treeUri);
        return documentFile != null && documentFile.getName() != null ? documentFile.getName() : "Unknown Folder";
    }

    private void setupSpinner() {
        ArrayAdapter<String> adapter = new ArrayAdapter<>(this,
                android.R.layout.simple_spinner_item, SCHEDULE_OPTIONS);
        adapter.setDropDownViewResource(android.R.layout.simple_spinner_dropdown_item);
        spinnerSchedule.setAdapter(adapter);

        int schedulePref = sharedPreferences.getInt(KEY_SCHEDULE_PREF, SCHEDULE_NEVER);
        if (schedulePref < 0 || schedulePref >= SCHEDULE_OPTIONS.length) {
            schedulePref = SCHEDULE_NEVER;
        }
        spinnerSchedule.setSelection(schedulePref);

        spinnerSchedule.setOnItemSelectedListener(new AdapterView.OnItemSelectedListener() {
            @Override
            public void onItemSelected(AdapterView<?> parent, View view, int position, long id) {
                sharedPreferences.edit().putInt(KEY_SCHEDULE_PREF, position).apply();
                savePreferences(); // Save all current settings as worker will need them

                if (position == SCHEDULE_NEVER) {
                    configureScheduledSync(SCHEDULE_NEVER);
                } else { // A schedule (12 Hours or 15 Mins Test) is selected
                    if (validateInputs(false)) {
                        configureScheduledSync(position);
                    } else {
                        Toast.makeText(MainActivity.this, "Please fill all S3 details and select a folder to enable scheduled sync.", Toast.LENGTH_LONG).show();
                        // Revert spinner to "Never" which will re-trigger onItemSelected for SCHEDULE_NEVER
                        spinnerSchedule.setSelection(SCHEDULE_NEVER);
                    }
                }
            }

            @Override
            public void onNothingSelected(AdapterView<?> parent) {}
        });
    }

    private void configureScheduledSync(int scheduleType) {
        WorkManager workManager = WorkManager.getInstance(getApplicationContext());

        if (scheduleType != SCHEDULE_NEVER && !validateInputs(false)) {
            Log.w(TAG, "Cannot schedule sync (type " + scheduleType + "): inputs invalid. Reverting to Never.");
            if (spinnerSchedule.getSelectedItemPosition() != SCHEDULE_NEVER) {
                spinnerSchedule.setSelection(SCHEDULE_NEVER); // This will re-trigger onItemSelected
            }
            // Ensure preference is also set to Never if not already done by setSelection's re-trigger
            if (sharedPreferences.getInt(KEY_SCHEDULE_PREF,SCHEDULE_NEVER) != SCHEDULE_NEVER) {
                sharedPreferences.edit().putInt(KEY_SCHEDULE_PREF, SCHEDULE_NEVER).apply();
            }
            workManager.cancelUniqueWork(S3SyncWorker.WORK_TAG);
            updateStatus("Scheduled sync disabled due to invalid config. Please check settings.");
            return;
        }

        Constraints constraints;
        PeriodicWorkRequest syncRequest = null;
        String scheduleDescription = "";

        switch (scheduleType) {
            case SCHEDULE_NEVER:
                workManager.cancelUniqueWork(S3SyncWorker.WORK_TAG);
                updateStatus("Scheduled sync disabled.");
                Log.i(TAG, "Scheduled S3 sync cancelled (set to Never).");
                return;

            case SCHEDULE_EVERY_12_HOURS:
                constraints = new Constraints.Builder()
                        .setRequiredNetworkType(NetworkType.UNMETERED) // Wi-Fi or unmetered mobile
                        // .setRequiresStorageNotLow(true) // Good to have
                        // .setRequiresDeviceIdle(true) // Consider if sync is very resource intensive and can wait for idle
                        .build();
                syncRequest = new PeriodicWorkRequest.Builder(S3SyncWorker.class, 12, TimeUnit.HOURS)
                        .setConstraints(constraints)
                        .addTag(S3SyncWorker.WORK_TAG)
                        .build();
                scheduleDescription = "Sync scheduled approx. every 12 hours (Wi-Fi only).";
                Log.i(TAG, "12-Hour S3 sync scheduling.");
                break;

            case SCHEDULE_EVERY_15_MINUTES_TEST:
                constraints = new Constraints.Builder()
                        .setRequiredNetworkType(NetworkType.CONNECTED) // Any network for easier testing
                        .build();
                syncRequest = new PeriodicWorkRequest.Builder(S3SyncWorker.class, PeriodicWorkRequest.MIN_PERIODIC_INTERVAL_MILLIS, TimeUnit.MILLISECONDS)
                        .setConstraints(constraints)
                        .addTag(S3SyncWorker.WORK_TAG)
                        .build();
                scheduleDescription = "Test sync scheduled approx. every 15 minutes (any network).";
                Log.i(TAG, "Test S3 sync (every 15 mins) scheduling.");
                break;

            default:
                Log.w(TAG, "Unknown scheduleType: " + scheduleType + ". Cancelling any existing scheduled sync.");
                workManager.cancelUniqueWork(S3SyncWorker.WORK_TAG);
                updateStatus("Scheduled sync disabled (unknown schedule type).");
                return;
        }

        if (syncRequest != null) {
            workManager.enqueueUniquePeriodicWork(
                    S3SyncWorker.WORK_TAG,
                    ExistingPeriodicWorkPolicy.REPLACE,
                    syncRequest);
            updateStatus(scheduleDescription);
            Log.i(TAG, "Scheduled S3 sync enqueued: " + scheduleDescription);
        }
    }


    private boolean validateInputs() {
        return validateInputs(true);
    }

    private boolean validateInputs(boolean showToast) {
        if (TextUtils.isEmpty(etAccessKey.getText()) ||
                TextUtils.isEmpty(etSecretKey.getText()) ||
                TextUtils.isEmpty(etEndpoint.getText()) ||
                TextUtils.isEmpty(etBucketName.getText()) ||
                localFolderUri == null) {
            if (showToast) {
                Toast.makeText(this, "Please fill all S3 details and select a local folder.", Toast.LENGTH_LONG).show();
            }
            return false;
        }
        String endpoint = etEndpoint.getText().toString().trim();
        if (endpoint.startsWith("http://") || endpoint.startsWith("https://")) {
            if (showToast) {
                Toast.makeText(this, "Endpoint should not include http:// or https://", Toast.LENGTH_LONG).show();
            }
            return false;
        }
        if (endpoint.contains("/") || endpoint.contains("?") || endpoint.contains("#")) {
            if (showToast) {
                Toast.makeText(this, "Endpoint should be just the hostname (and port if needed)", Toast.LENGTH_LONG).show();
            }
            return false;
        }
        return true;
    }

    private void loadPreferences() {
        etAccessKey.setText(sharedPreferences.getString(KEY_ACCESS_KEY, ""));
        etSecretKey.setText(sharedPreferences.getString(KEY_SECRET_KEY, ""));
        etEndpoint.setText(sharedPreferences.getString(KEY_ENDPOINT, ""));
        etBucketName.setText(sharedPreferences.getString(KEY_BUCKET_NAME, ""));
        etBucketPath.setText(sharedPreferences.getString(KEY_BUCKET_PATH, ""));

        String folderUriStr = sharedPreferences.getString(KEY_LOCAL_FOLDER_URI, null);
        if (folderUriStr != null) {
            localFolderUri = Uri.parse(folderUriStr);
            try {
                DocumentFile documentFile = DocumentFile.fromTreeUri(this, localFolderUri);
                if (documentFile != null && documentFile.canRead() && documentFile.getName() != null) {
                    tvSelectedFolder.setText("Selected: " + getPathFromUri(localFolderUri));
                } else {
                    tvSelectedFolder.setText("Permission lost or folder invalid. Please re-select.");
                    localFolderUri = null;
                    sharedPreferences.edit().remove(KEY_LOCAL_FOLDER_URI).apply();
                }
            } catch (Exception e) {
                Log.e(TAG, "Error accessing persisted folder URI", e);
                tvSelectedFolder.setText("Error with saved folder. Please re-select.");
                localFolderUri = null;
                sharedPreferences.edit().remove(KEY_LOCAL_FOLDER_URI).apply();
            }
        } else {
            tvSelectedFolder.setText("No folder selected");
        }
        // Spinner selection is handled in setupSpinner after its adapter is set
    }

    private void savePreferences() {
        SharedPreferences.Editor editor = sharedPreferences.edit();
        editor.putString(KEY_ACCESS_KEY, etAccessKey.getText().toString().trim());
        editor.putString(KEY_SECRET_KEY, etSecretKey.getText().toString().trim());
        editor.putString(KEY_ENDPOINT, etEndpoint.getText().toString().trim());
        editor.putString(KEY_BUCKET_NAME, etBucketName.getText().toString().trim());
        editor.putString(KEY_BUCKET_PATH, etBucketPath.getText().toString().trim());
        if (localFolderUri != null) {
            editor.putString(KEY_LOCAL_FOLDER_URI, localFolderUri.toString());
        } else {
            editor.remove(KEY_LOCAL_FOLDER_URI);
        }
        editor.putInt(KEY_SCHEDULE_PREF, spinnerSchedule.getSelectedItemPosition());
        editor.apply();
        Log.d(TAG, "Preferences saved.");
    }

    private void updateStatus(String message) {
        Log.d(TAG, "Status: " + message);
        mainThreadHandler.post(() -> tvStatus.setText("Status: " + message));
    }

    private void performSyncNow() {
        updateStatus("Manual sync initiated...");
        btnSyncNow.setEnabled(false);
        // savePreferences() already called by the click listener.

        OneTimeWorkRequest oneTimeSyncRequest =
                new OneTimeWorkRequest.Builder(S3SyncWorker.class)
                        .addTag("MANUAL_SYNC_NOW_TAG")
                        // .setExpedited(OutOfQuotaPolicy.RUN_AS_NON_EXPEDITED_WORK_REQUEST) // Consider for faster manual sync start
                        .build();

        WorkManager.getInstance(getApplicationContext()).enqueue(oneTimeSyncRequest);

        WorkManager.getInstance(getApplicationContext()).getWorkInfoByIdLiveData(oneTimeSyncRequest.getId())
                .observe(this, workInfo -> {
                    if (workInfo != null) {
                        Log.d(TAG, "Manual Sync WorkInfo state: " + workInfo.getState());
                        switch (workInfo.getState()) {
                            case SUCCEEDED:
                                updateStatus("Manual sync completed successfully.");
                                break;
                            case FAILED:
                                updateStatus("Manual sync failed. Check logs for details.");
                                break;
                            case CANCELLED:
                                updateStatus("Manual sync cancelled.");
                                break;
                            case RUNNING:
                                updateStatus("Manual sync in progress...");
                                break;
                            case ENQUEUED:
                                updateStatus("Manual sync enqueued by WorkManager.");
                                break;
                            default: // BLOCKED
                                if(btnSyncNow.isEnabled()){
                                    updateStatus("Manual sync status: " + workInfo.getState());
                                }
                                break;
                        }
                        if (workInfo.getState().isFinished()) {
                            btnSyncNow.setEnabled(true);
                            WorkManager.getInstance(getApplicationContext()).getWorkInfoByIdLiveData(oneTimeSyncRequest.getId()).removeObservers(this);
                        }
                    }
                });
    }

    @Override
    protected void onPause() {
        super.onPause();
        savePreferences();
    }

    @Override
    protected void onDestroy() {
        super.onDestroy();
    }
}