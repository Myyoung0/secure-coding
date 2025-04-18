// 문서가 로드된 후 실행
document.addEventListener('DOMContentLoaded', function() {
    
    // 숫자 포맷 함수
    function formatNumber(number) {
        return new Intl.NumberFormat('ko-KR').format(number);
    }
    
    // 가격 포맷 적용 (클래스로 적용할 경우)
    const priceElements = document.querySelectorAll('.format-price');
    priceElements.forEach(function(element) {
        const price = parseInt(element.textContent.replace(/[^0-9]/g, ''), 10);
        if (!isNaN(price)) {
            element.textContent = formatNumber(price) + '원';
        }
    });
    
    // 토스트 메시지 표시 함수
    function showToast(message, type = 'success') {
        const toastContainer = document.createElement('div');
        toastContainer.className = 'toast-container position-fixed bottom-0 end-0 p-3';
        
        const toast = document.createElement('div');
        toast.className = `toast align-items-center text-white bg-${type} border-0`;
        toast.setAttribute('role', 'alert');
        toast.setAttribute('aria-live', 'assertive');
        toast.setAttribute('aria-atomic', 'true');
        
        const toastBody = document.createElement('div');
        toastBody.className = 'd-flex';
        
        const messageDiv = document.createElement('div');
        messageDiv.className = 'toast-body';
        messageDiv.textContent = message;
        
        const closeButton = document.createElement('button');
        closeButton.type = 'button';
        closeButton.className = 'btn-close btn-close-white me-2 m-auto';
        closeButton.setAttribute('data-bs-dismiss', 'toast');
        closeButton.setAttribute('aria-label', '닫기');
        
        toastBody.appendChild(messageDiv);
        toastBody.appendChild(closeButton);
        toast.appendChild(toastBody);
        toastContainer.appendChild(toast);
        
        document.body.appendChild(toastContainer);
        
        const bsToast = new bootstrap.Toast(toast);
        bsToast.show();
        
        toast.addEventListener('hidden.bs.toast', function() {
            document.body.removeChild(toastContainer);
        });
    }
    
    // 전역에서 사용할 수 있도록 window 객체에 추가
    window.showToast = showToast;
    
    // 이미지 프리뷰 기능 (이미지 업로드 시)
    const imageInput = document.getElementById('images');
    if (imageInput) {
        imageInput.addEventListener('change', function() {
            const previewContainer = document.getElementById('imagePreview');
            if (previewContainer) {
                previewContainer.innerHTML = '';
                
                const files = this.files;
                for (let i = 0; i < files.length; i++) {
                    const file = files[i];
                    if (!file.type.startsWith('image/')) continue;
                    
                    const reader = new FileReader();
                    const col = document.createElement('div');
                    col.className = 'col-4 col-md-3 mb-2';
                    
                    reader.onload = function(e) {
                        col.innerHTML = `
                            <div class="card">
                                <img src="${e.target.result}" class="card-img-top" alt="미리보기" style="height: 150px; object-fit: cover;">
                            </div>
                        `;
                        previewContainer.appendChild(col);
                    };
                    
                    reader.readAsDataURL(file);
                }
            }
        });
    }
}); 