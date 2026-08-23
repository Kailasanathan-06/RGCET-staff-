"""
Setup script for Google Cloud Storage.
Run this to configure your Google Cloud bucket for file uploads.

Prerequisites:
1. Create a Google Cloud project at https://console.cloud.google.com
2. Enable Cloud Storage API
3. Create a bucket
4. Create a service account with Storage Admin role
5. Download the JSON key file

Usage:
    python setup_gcloud_storage.py
"""
import os
import json


def setup_gcloud():
    print("=" * 60)
    print("Google Cloud Storage Setup for RGCET Project")
    print("=" * 60)
    print()

    # Get bucket name
    bucket_name = input("Enter your Google Cloud Storage bucket name: ").strip()
    if not bucket_name:
        print("Error: Bucket name is required!")
        return

    # Get project ID
    project_id = input("Enter your Google Cloud project ID: ").strip()
    if not project_id:
        print("Error: Project ID is required!")
        return

    # Get service account email
    service_account = input("Enter your service account email: ").strip()
    if not service_account:
        print("Error: Service account email is required!")
        return

    # Create .env additions
    env_additions = f"""
# Google Cloud Storage Configuration
GS_BUCKET_NAME={bucket_name}
GS_PROJECT_ID={project_id}
GS_CLIENT_EMAIL={service_account}
GS_DEFAULT_ACL=publicRead
GS_QUERYSTRING_AUTH=False
"""

    print()
    print("=" * 60)
    print("Add these to your Vercel environment variables:")
    print("=" * 60)
    print(env_additions)

    # Save to a file
    with open("gcloud_env.txt", "w") as f:
        f.write(env_additions)

    print()
    print("Configuration saved to gcloud_env.txt")
    print()
    print("Next steps:")
    print("1. Add these environment variables to Vercel")
    print("2. Uncomment Google Cloud Storage lines in config/settings/vercel.py")
    print("3. Deploy again to Vercel")


if __name__ == "__main__":
    setup_gcloud()
