"""
Google Cloud Storage Setup Script for RGCET Project
====================================================
This script guides you through setting up Google Cloud Storage
to store uploaded PDFs, documents, and files.

Free Tier: 15GB (same as your Gmail account!)

Usage:
    python setup_gcloud.py
"""
import os
import json
import webbrowser


def print_header():
    print("=" * 70)
    print("   Google Cloud Storage Setup for RGCET Project")
    print("   Free Tier: 15GB storage for uploaded files!")
    print("=" * 70)
    print()


def step1_create_project():
    print("STEP 1: Create Google Cloud Project")
    print("-" * 40)
    print()
    print("1. Go to: https://console.cloud.google.com")
    print("2. Sign in with your Gmail account")
    print("3. Click 'Select a project' → 'New Project'")
    print("4. Name: 'rgcet-uploads'")
    print("5. Click 'Create'")
    print()
    input("Press Enter when done...")
    print()

    project_id = input("Enter your Project ID (from Google Cloud Console): ").strip()
    return project_id


def step2_enable_storage():
    print("STEP 2: Enable Cloud Storage API")
    print("-" * 40)
    print()
    print("1. In Google Cloud Console, go to:")
    print("   https://console.cloud.google.com/apis/library/storage-api.googleapis.com")
    print("2. Click 'Enable'")
    print()
    input("Press Enter when done...")
    print()


def step3_create_bucket():
    print("STEP 3: Create Storage Bucket")
    print("-" * 40)
    print()
    print("1. Go to: https://console.cloud.google.com/storage/browser")
    print("2. Click 'Create Bucket'")
    print("3. Name: 'rgcet-uploads' (must be globally unique)")
    print("4. Location: 'Region' → 'us-central1' (or closest to you)")
    print("5. Storage class: 'Standard'")
    print("6. Access control: 'Uniform'")
    print("7. Click 'Create'")
    print()
    input("Press Enter when done...")
    print()

    bucket_name = input("Enter your bucket name: ").strip()
    return bucket_name


def step4_make_public():
    print("STEP 4: Make Bucket Public (for file access)")
    print("-" * 40)
    print()
    print("1. Go to your bucket in Cloud Storage")
    print("2. Click 'Permissions' tab")
    print("3. Click 'Grant Access'")
    print("4. Add members: 'allUsers'")
    print("5. Role: 'Storage Object Viewer'")
    print("6. Click 'Save'")
    print()
    input("Press Enter when done...")
    print()


def step5_create_service_account():
    print("STEP 5: Create Service Account (for file uploads)")
    print("-" * 40)
    print()
    print("1. Go to: https://console.cloud.google.com/iam-admin/serviceaccounts")
    print("2. Click 'Create Service Account'")
    print("3. Name: 'rgcet-uploads'")
    print("4. Click 'Create and Continue'")
    print("5. Role: 'Storage Admin'")
    print("6. Click 'Done'")
    print()
    input("Press Enter when done...")
    print()

    service_account_email = input("Enter service account email: ").strip()
    return service_account_email


def step6_create_key():
    print("STEP 6: Create Service Account Key")
    print("-" * 40)
    print()
    print("1. Click on your service account name")
    print("2. Go to 'Keys' tab")
    print("3. Click 'Add Key' → 'Create new key'")
    print("4. Select 'JSON'")
    print("5. Click 'Create'")
    print("6. Save the JSON file somewhere safe!")
    print()
    input("Press Enter when done...")
    print()

    json_path = input("Enter the path to the JSON key file: ").strip()
    if not os.path.exists(json_path):
        print(f"Error: File not found at {json_path}")
        return None

    with open(json_path, 'r') as f:
        key_data = json.load(f)

    return key_data


def generate_env_file(bucket_name, project_id, service_account_email, key_data):
    print("STEP 7: Generating Environment Variables")
    print("-" * 40)
    print()

    env_content = f"""
# Google Cloud Storage Configuration
# Add these to your Vercel environment variables

GS_BUCKET_NAME={bucket_name}
GS_PROJECT_ID={project_id}
GS_CLIENT_EMAIL={service_account_email}
GS_PRIVATE_KEY_ID={key_data.get('private_key_id', '')}
GS_PRIVATE_KEY={key_data.get('private_key', '')}
GS_CLIENT_ID={key_data.get('client_id', '')}
"""

    # Save to file
    with open("gcloud_env.txt", "w") as f:
        f.write(env_content)

    print("Environment variables saved to: gcloud_env.txt")
    print()
    print("=" * 70)
    print("   IMPORTANT: Copy these values to Vercel!")
    print("=" * 70)
    print()
    print(env_content)


def main():
    print_header()

    print("This script will set up Google Cloud Storage for your project.")
    print("You'll need a Gmail account (you already have one!).")
    print()
    input("Press Enter to start...")
    print()

    # Run through steps
    project_id = step1_create_project()
    step2_enable_storage()
    bucket_name = step3_create_bucket()
    step4_make_public()
    service_account_email = step5_create_service_account()
    key_data = step6_create_key()

    if key_data:
        generate_env_file(bucket_name, project_id, service_account_email, key_data)
        print()
        print("=" * 70)
        print("   Setup Complete!")
        print("=" * 70)
        print()
        print("Next steps:")
        print("1. Add the environment variables to Vercel")
        print("2. Deploy your project to Vercel")
        print("3. Upload files - they'll be stored in Google Cloud Storage!")
        print()
        print("Your files will be accessible at:")
        print(f"  https://storage.googleapis.com/{bucket_name}/media/...")
        print()
    else:
        print("Error: Could not read key file. Please try again.")


if __name__ == "__main__":
    main()
