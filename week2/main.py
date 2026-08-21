

from minio import Minio
from minio.error import S3Error

# ----- Cấu hình kết nối MinIO -----
client = Minio(
    "localhost:9000",
    access_key="Admin",      
    secret_key="Admin@123",     
    secure=False                      
)

BUCKET_NAME = "my-bucket"


def upload_image(local_file_path: str, object_name: str) -> bool:
    """
    Upload 1 file ảnh lên MinIO bucket.
    """
    try:
        # Kiểm tra bucket tồn tại, nếu chưa thì tạo mới
        if not client.bucket_exists(BUCKET_NAME):
            client.make_bucket(BUCKET_NAME)
            print(f"Đã tạo bucket mới: {BUCKET_NAME}")

        # Upload file lên bucket
        client.fput_object(
            bucket_name=BUCKET_NAME,
            object_name=object_name,
            file_path=local_file_path,
        )
        print(f"Upload thành công: {local_file_path} -> {BUCKET_NAME}/{object_name}")
        return True

    except S3Error as e:
        print(f"Lỗi khi upload: {e}")
        return False
    except FileNotFoundError:
        print(f"Không tìm thấy file: {local_file_path}")
        return False


def download_image(object_name: str, save_path: str) -> bool:
    """
    Download 1 object từ MinIO bucket về máy local.
    """
    try:
        client.fget_object(
            bucket_name=BUCKET_NAME,
            object_name=object_name,
            file_path=save_path,
        )
        print(f"Download thành công: {BUCKET_NAME}/{object_name} -> {save_path}")
        return True

    except S3Error as e:
        print(f"Lỗi khi download: {e}")
        return False


# ----- Test thử với ảnh thật -----
if __name__ == "__main__":
    # Test upload
    upload_image(
        local_file_path="D:/Images/bucket.png",
        object_name="images/test-image.jpg",
    )

    # Test download
    download_image(
        object_name="images/test-image.jpg",
        save_path="C:/Users/ASUS/Downloads/test-image-downloaded.jpg",
    )