document.addEventListener('alpine:init', () => {
    Alpine.data('bingkaiApp', () => ({
        isAuthenticated: false,
        isAuthChecking: true,
        currentUser: null,
        loginForm: {
            username: 'admin',
            password: 'admin123'
        },
        loginLoading: false,
        loginError: '',

        currentView: 'gallery',
        isDarkMode: false,
        isMobileMenuOpen: false,

        photos: [],
        groupedPhotos: [],
        totalPhotos: 0,
        page: 1,
        limit: 50,
        totalPages: 1,
        hasNextPage: false,
        hasPrevPage: false,
        isLoadingPhotos: false,

        searchQuery: '',
        sortBy: 'date_desc',
        selectedFolderId: null,

        folders: [],
        isLoadingFolders: false,
        isAddFolderModalOpen: false,
        newFolderPath: '',
        newFolderName: '',
        isSubmittingFolder: false,
        isScanningFolder: false,
        activeScanningId: null,

        isViewerOpen: false,
        activePhoto: null,
        activePhotoIndex: -1,
        photoDetail: null,
        isLoadingDetail: false,

        dashboardStats: null,
        isLoadingDashboard: false,
        systemInfo: null,

        toasts: [],

        async init() {
            this.initTheme();
            this.initEventListeners();
            await this.checkAuthStatus();
            if (this.isAuthenticated) {
                await this.loadInitialData();
            }
            this.isAuthChecking = false;
        },

        initTheme() {
            const savedTheme = localStorage.getItem('bingkai_theme');
            if (savedTheme === 'dark' || (!savedTheme && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
                this.isDarkMode = true;
                document.documentElement.classList.add('dark');
            } else {
                this.isDarkMode = false;
                document.documentElement.classList.remove('dark');
            }
        },

        toggleDarkMode() {
            this.isDarkMode = !this.isDarkMode;
            if (this.isDarkMode) {
                document.documentElement.classList.add('dark');
                localStorage.setItem('bingkai_theme', 'dark');
            } else {
                document.documentElement.classList.remove('dark');
                localStorage.setItem('bingkai_theme', 'light');
            }
        },

        initEventListeners() {
            window.addEventListener('bingkai-unauthorized', () => {
                this.isAuthenticated = false;
                this.currentUser = null;
                this.showToast('Sesi Anda telah berakhir. Silakan login kembali.', 'error');
            });

            window.addEventListener('keydown', (e) => {
                if (!this.isViewerOpen) return;
                if (e.key === 'Escape') this.closeViewer();
                if (e.key === 'ArrowRight') this.nextPhoto();
                if (e.key === 'ArrowLeft') this.prevPhoto();
            });
        },

        showToast(message, type = 'info') {
            const id = Date.now();
            this.toasts.push({ id, message, type });
            setTimeout(() => {
                this.toasts = this.toasts.filter(t => t.id !== id);
            }, 4000);
        },

        async checkAuthStatus() {
            try {
                const user = await BingkaiAPI.getMe();
                this.currentUser = user;
                this.isAuthenticated = true;
            } catch (e) {
                this.isAuthenticated = false;
                this.currentUser = null;
            }
        },

        async login() {
            this.loginLoading = true;
            this.loginError = '';
            try {
                const user = await BingkaiAPI.login(this.loginForm.username, this.loginForm.password);
                this.currentUser = user;
                this.isAuthenticated = true;
                this.showToast(`Selamat datang kembali, ${user.username}!`, 'success');
                await this.loadInitialData();
            } catch (err) {
                this.loginError = err.message || 'Login gagal. Periksa username dan password.';
            } finally {
                this.loginLoading = false;
            }
        },

        async logout() {
            try {
                await BingkaiAPI.logout();
            } catch (e) {
            }
            this.isAuthenticated = false;
            this.currentUser = null;
            this.showToast('Anda telah logout.', 'info');
        },

        async loadInitialData() {
            await Promise.all([
                this.loadFolders(),
                this.loadPhotos(),
                this.loadSystemInfo()
            ]);
            this.$nextTick(() => {
                if (window.lucide) window.lucide.createIcons();
            });
        },

        switchView(viewName) {
            this.currentView = viewName;
            this.isMobileMenuOpen = false;
            if (viewName === 'gallery') {
                this.selectedFolderId = null;
                this.loadPhotos(1);
            } else if (viewName === 'favorites') {
                this.loadPhotos(1);
            } else if (viewName === 'folders') {
                this.loadFolders();
            } else if (viewName === 'dashboard') {
                this.loadDashboard();
            } else if (viewName === 'settings') {
                this.loadSystemInfo();
                this.loadFolders();
            }
            this.$nextTick(() => {
                if (window.lucide) window.lucide.createIcons();
            });
        },

        async loadPhotos(targetPage = 1) {
            this.isLoadingPhotos = true;
            try {
                const isFavorite = this.currentView === 'favorites';
                const result = await BingkaiAPI.getPhotos({
                    page: targetPage,
                    limit: this.limit,
                    folderId: this.selectedFolderId,
                    favorite: isFavorite,
                    q: this.searchQuery,
                    sort: this.sortBy
                });

                this.photos = result.items;
                this.groupedPhotos = GalleryUtils.groupPhotosByDate(this.photos);
                this.totalPhotos = result.total;
                this.page = result.page;
                this.totalPages = result.total_pages;
                this.hasNextPage = result.has_next;
                this.hasPrevPage = result.has_prev;
            } catch (err) {
                this.showToast(err.message || 'Gagal memuat galeri foto.', 'error');
            } finally {
                this.isLoadingPhotos = false;
                this.$nextTick(() => {
                    if (window.lucide) window.lucide.createIcons();
                });
            }
        },

        onSearchInput() {
            clearTimeout(this._searchTimer);
            this._searchTimer = setTimeout(() => {
                this.loadPhotos(1);
            }, 350);
        },

        onSortChange() {
            this.loadPhotos(1);
        },

        filterByFolder(folderId) {
            this.selectedFolderId = folderId;
            this.currentView = 'gallery';
            this.loadPhotos(1);
        },

        openViewer(photo, index) {
            this.activePhoto = photo;
            this.activePhotoIndex = index;
            this.isViewerOpen = true;
            this.loadPhotoDetail(photo.id);
            this.$nextTick(() => {
                if (window.lucide) window.lucide.createIcons();
            });
        },

        closeViewer() {
            this.isViewerOpen = false;
            this.activePhoto = null;
            this.photoDetail = null;
        },

        async loadPhotoDetail(photoId) {
            this.isLoadingDetail = true;
            try {
                this.photoDetail = await BingkaiAPI.getPhotoDetail(photoId);
            } catch (e) {
                console.error(e);
            } finally {
                this.isLoadingDetail = false;
            }
        },

        nextPhoto() {
            if (this.activePhotoIndex < this.photos.length - 1) {
                this.activePhotoIndex++;
                this.activePhoto = this.photos[this.activePhotoIndex];
                this.loadPhotoDetail(this.activePhoto.id);
            }
        },

        prevPhoto() {
            if (this.activePhotoIndex > 0) {
                this.activePhotoIndex--;
                this.activePhoto = this.photos[this.activePhotoIndex];
                this.loadPhotoDetail(this.activePhoto.id);
            }
        },

        async toggleFavoriteActive() {
            if (!this.activePhoto) return;
            try {
                const updated = await BingkaiAPI.toggleFavorite(this.activePhoto.id);
                this.activePhoto.favorite = updated.favorite;
                if (this.photoDetail) this.photoDetail.favorite = updated.favorite;
                
                const idx = this.photos.findIndex(p => p.id === updated.id);
                if (idx !== -1) {
                    this.photos[idx].favorite = updated.favorite;
                }
                this.showToast(updated.favorite ? 'Ditambahkan ke Favorit ❤️' : 'Dihapus dari Favorit', 'info');
            } catch (err) {
                this.showToast(err.message, 'error');
            }
        },

        async loadFolders() {
            this.isLoadingFolders = true;
            try {
                this.folders = await BingkaiAPI.getFolders();
            } catch (err) {
                this.showToast(err.message || 'Gagal mengambil daftar folder.', 'error');
            } finally {
                this.isLoadingFolders = false;
            }
        },

        async submitNewFolder() {
            if (!this.newFolderPath.trim()) {
                this.showToast('Path folder tidak boleh kosong.', 'error');
                return;
            }
            this.isSubmittingFolder = true;
            try {
                const newFolder = await BingkaiAPI.addFolder(this.newFolderPath.trim(), this.newFolderName.trim() || null);
                this.showToast(`Folder '${newFolder.name}' berhasil ditambahkan!`, 'success');
                this.newFolderPath = '';
                this.newFolderName = '';
                this.isAddFolderModalOpen = false;
                await this.loadFolders();

                await this.triggerFolderScan(newFolder.id);
            } catch (err) {
                this.showToast(err.message, 'error');
            } finally {
                this.isSubmittingFolder = false;
            }
        },

        async triggerFolderScan(folderId) {
            this.isScanningFolder = true;
            this.activeScanningId = folderId;
            this.showToast('Memulai pemindaian folder...', 'info');
            try {
                const result = await BingkaiAPI.scanFolder(folderId);
                this.showToast(result.message, 'success');
                await Promise.all([
                    this.loadFolders(),
                    this.loadPhotos(this.page)
                ]);
            } catch (err) {
                this.showToast(err.message || 'Gagal memindai folder.', 'error');
            } finally {
                this.isScanningFolder = false;
                this.activeScanningId = null;
            }
        },

        async deleteFolder(folder) {
            if (!confirm(`Hapus folder "${folder.name}" dari monitoring Bingkai?\n\n(File foto fisik di komputer TIDAK akan terhapus).`)) {
                return;
            }
            try {
                await BingkaiAPI.deleteFolder(folder.id);
                this.showToast(`Folder "${folder.name}" dihapus dari monitoring.`, 'success');
                await this.loadFolders();
                if (this.selectedFolderId === folder.id) {
                    this.selectedFolderId = null;
                }
                await this.loadPhotos(1);
            } catch (err) {
                this.showToast(err.message, 'error');
            }
        },

        async loadDashboard() {
            this.isLoadingDashboard = true;
            try {
                this.dashboardStats = await BingkaiAPI.getDashboard();
            } catch (err) {
                this.showToast(err.message || 'Gagal memuat statistik dashboard.', 'error');
            } finally {
                this.isLoadingDashboard = false;
            }
        },

        async loadSystemInfo() {
            try {
                this.systemInfo = await BingkaiAPI.getSystemInfo();
            } catch (e) {
                console.error(e);
            }
        },

        formatSize(bytes) {
            return GalleryUtils.formatFileSize(bytes);
        },

        formatDate(dateStr) {
            return GalleryUtils.formatDateTime(dateStr);
        },

        getThumbUrl(photoId) {
            return BingkaiAPI.getThumbnailUrl(photoId);
        },

        getOrigUrl(photoId) {
            return BingkaiAPI.getOriginalUrl(photoId);
        }
    }));
});
