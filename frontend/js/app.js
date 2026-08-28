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
        isShortcutsModalOpen: false,

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
        zoomLevel: 1,
        rotationDeg: 0,

        isRenameModalOpen: false,
        renameInputName: '',
        isRenaming: false,

        isMoveModalOpen: false,
        targetMoveFolderId: null,
        isMoving: false,

        isAddToAlbumModalOpen: false,

        trashPhotos: [],
        trashTotal: 0,
        trashPage: 1,
        trashTotalPages: 1,
        isLoadingTrash: false,

        albums: [],
        activeAlbum: null,
        isLoadingAlbums: false,
        isCreateAlbumModalOpen: false,
        newAlbumName: '',
        newAlbumDesc: '',
        isSubmittingAlbum: false,

        duplicateGroups: [],
        isLoadingDuplicates: false,

        swipePhotos: [],
        swipeIndex: 0,
        swipeDeltaX: 0,
        swipeDeltaY: 0,
        swipeRotateDeg: 0,
        swipeCardStatus: '',
        swipeIsDragging: false,
        isSwipeAnimating: false,
        swipeStartX: 0,
        swipeStartY: 0,
        swipeHistory: [],
        swipeSavedCount: 0,
        swipeTrashedCount: 0,

        gamepadConnected: false,
        gamepadName: '',
        focusedPhotoIndex: 0,
        _gamepadPollId: null,
        _lastGamepadAction: 0,

        dashboardStats: null,
        isLoadingDashboard: false,
        systemInfo: null,
        qrCodes: {},
        isQrModalOpen: false,
        activeQrUrl: '',

        toasts: [],

        async init() {
            this.initTheme();
            this.initEventListeners();
            this.initGamepad();
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
                if (e.key === '?' && !this.isRenameModalOpen && !this.isAddFolderModalOpen && !this.isCreateAlbumModalOpen && !this.isQrModalOpen) {
                    this.isShortcutsModalOpen = !this.isShortcutsModalOpen;
                    return;
                }

                if (this.currentView === 'swipe') {
                    if (this.isShortcutsModalOpen || this.isQrModalOpen) return;
                    if (e.key === 'ArrowRight') {
                        e.preventDefault();
                        this.executeSwipeRight();
                    } else if (e.key === 'ArrowLeft') {
                        e.preventDefault();
                        this.executeSwipeLeft();
                    } else if (e.key === 'ArrowDown' || e.key === ' ') {
                        e.preventDefault();
                        this.executeSwipeSkip();
                    } else if (e.key === 'Backspace' || e.key === 'u' || e.key === 'U') {
                        e.preventDefault();
                        this.undoLastSwipe();
                    }
                    return;
                }

                if (!this.isViewerOpen) return;
                if (this.isRenameModalOpen || this.isMoveModalOpen || this.isAddToAlbumModalOpen || this.isShortcutsModalOpen || this.isQrModalOpen) return;

                if (e.key === 'Escape') this.closeViewer();
                if (e.key === 'ArrowRight') this.nextPhoto();
                if (e.key === 'ArrowLeft') this.prevPhoto();
                if (e.key === '+' || e.key === '=') this.zoomIn();
                if (e.key === '-' || e.key === '_') this.zoomOut();
                if (e.key === '0') this.resetZoom();
                if (e.key === 'r' || e.key === 'R') this.rotatePhoto();
                if (e.key === 'f' || e.key === 'F') this.toggleFavoriteActive();
                if (e.key === 'y' || e.key === 'Y' || e.key === 'F2') {
                    e.preventDefault();
                    this.openRenameModal();
                }
                if (e.key === 'm' || e.key === 'M') {
                    e.preventDefault();
                    this.openMoveModal();
                }
                if (e.key === 'a' || e.key === 'A') {
                    e.preventDefault();
                    this.isAddToAlbumModalOpen = true;
                }
                if (e.key === 'Delete') {
                    e.preventDefault();
                    this.trashActivePhoto();
                }
            });

            window.addEventListener('mousemove', (e) => {
                if (this.swipeIsDragging) {
                    this.onDragMove(e.clientX, e.clientY);
                }
            });

            window.addEventListener('mouseup', () => {
                if (this.swipeIsDragging) {
                    this.onDragEnd();
                }
            });
        },

        initGamepad() {
            window.addEventListener('gamepadconnected', (e) => {
                this.gamepadConnected = true;
                this.gamepadName = e.gamepad.id.split('(')[0].trim() || 'Gamepad Controller';
                this.showToast(`Controller Terhubung: ${this.gamepadName}`, 'success');
                this.startGamepadLoop();
            });

            window.addEventListener('gamepaddisconnected', () => {
                this.gamepadConnected = false;
                this.gamepadName = '';
                this.showToast('Controller Terputus', 'info');
                if (this._gamepadPollId) {
                    cancelAnimationFrame(this._gamepadPollId);
                    this._gamepadPollId = null;
                }
            });

            const initialGamepads = navigator.getGamepads ? navigator.getGamepads() : [];
            for (const gp of initialGamepads) {
                if (gp) {
                    this.gamepadConnected = true;
                    this.gamepadName = gp.id.split('(')[0].trim() || 'Gamepad Controller';
                    this.startGamepadLoop();
                    break;
                }
            }
        },

        startGamepadLoop() {
            if (this._gamepadPollId) return;

            const poll = () => {
                const gamepads = navigator.getGamepads ? navigator.getGamepads() : [];
                let activeGp = null;
                for (const gp of gamepads) {
                    if (gp) {
                        activeGp = gp;
                        break;
                    }
                }

                if (activeGp) {
                    this.handleGamepadInput(activeGp);
                }

                this._gamepadPollId = requestAnimationFrame(poll);
            };

            this._gamepadPollId = requestAnimationFrame(poll);
        },

        handleGamepadInput(gp) {
            const now = Date.now();
            if (now - this._lastGamepadAction < 240) return;

            const bA = gp.buttons[0] && gp.buttons[0].pressed;
            const bB = gp.buttons[1] && gp.buttons[1].pressed;
            const bX = gp.buttons[2] && gp.buttons[2].pressed;
            const bY = gp.buttons[3] && gp.buttons[3].pressed;
            const bLB = gp.buttons[4] && gp.buttons[4].pressed;
            const bRB = gp.buttons[5] && gp.buttons[5].pressed;

            const dUp = gp.buttons[12] && gp.buttons[12].pressed || gp.axes[1] < -0.5;
            const dDown = gp.buttons[13] && gp.buttons[13].pressed || gp.axes[1] > 0.5;
            const dLeft = gp.buttons[14] && gp.buttons[14].pressed || gp.axes[0] < -0.5;
            const dRight = gp.buttons[15] && gp.buttons[15].pressed || gp.axes[0] > 0.5;

            if (this.currentView === 'swipe') {
                if (bA || dRight) {
                    this.executeSwipeRight();
                    this._lastGamepadAction = now;
                    return;
                }
                if (bB || dLeft) {
                    this.executeSwipeLeft();
                    this._lastGamepadAction = now;
                    return;
                }
                if (bY || dDown) {
                    this.executeSwipeSkip();
                    this._lastGamepadAction = now;
                    return;
                }
                if (bX) {
                    this.undoLastSwipe();
                    this._lastGamepadAction = now;
                    return;
                }
                return;
            }

            if (this.isViewerOpen) {
                if (bB) {
                    this.closeViewer();
                    this._lastGamepadAction = now;
                    return;
                }
                if (dRight || bRB) {
                    this.nextPhoto();
                    this._lastGamepadAction = now;
                    return;
                }
                if (dLeft || bLB) {
                    this.prevPhoto();
                    this._lastGamepadAction = now;
                    return;
                }
                if (bX) {
                    this.toggleFavoriteActive();
                    this._lastGamepadAction = now;
                    return;
                }
                if (bY) {
                    this.openRenameModal();
                    this._lastGamepadAction = now;
                    return;
                }
            } else {
                if (dRight) {
                    if (this.focusedPhotoIndex < this.photos.length - 1) {
                        this.focusedPhotoIndex++;
                        this._lastGamepadAction = now;
                    }
                    return;
                }
                if (dLeft) {
                    if (this.focusedPhotoIndex > 0) {
                        this.focusedPhotoIndex--;
                        this._lastGamepadAction = now;
                    }
                    return;
                }
                if (dDown) {
                    if (this.focusedPhotoIndex + 6 < this.photos.length) {
                        this.focusedPhotoIndex += 6;
                        this._lastGamepadAction = now;
                    }
                    return;
                }
                if (dUp) {
                    if (this.focusedPhotoIndex - 6 >= 0) {
                        this.focusedPhotoIndex -= 6;
                        this._lastGamepadAction = now;
                    }
                    return;
                }
                if (bA && this.photos[this.focusedPhotoIndex]) {
                    this.openViewer(this.photos[this.focusedPhotoIndex], this.focusedPhotoIndex);
                    this._lastGamepadAction = now;
                    return;
                }
                if (bX && this.photos[this.focusedPhotoIndex]) {
                    const p = this.photos[this.focusedPhotoIndex];
                    BingkaiAPI.toggleFavorite(p.id).then(updated => {
                        p.favorite = updated.favorite;
                        this.showToast(updated.favorite ? 'Ditambahkan ke Favorit' : 'Dihapus dari Favorit', 'info');
                    });
                    this._lastGamepadAction = now;
                    return;
                }
                if (bLB && this.hasPrevPage) {
                    this.loadPhotos(this.page - 1);
                    this._lastGamepadAction = now;
                    return;
                }
                if (bRB && this.hasNextPage) {
                    this.loadPhotos(this.page + 1);
                    this._lastGamepadAction = now;
                    return;
                }
            }
        },

        showToast(message, type = 'info') {
            const id = Date.now();
            this.toasts.push({ id, message, type });
            setTimeout(() => {
                this.toasts = this.toasts.filter(t => t.id !== id);
            }, 3000);
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
                this.loadAlbums(),
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
            } else if (viewName === 'swipe') {
                this.initSwipeDeck();
            } else if (viewName === 'folders') {
                this.loadFolders();
            } else if (viewName === 'albums') {
                this.loadAlbums();
            } else if (viewName === 'duplicates') {
                this.loadDuplicates();
            } else if (viewName === 'trash') {
                this.loadTrash(1);
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

        async initSwipeDeck() {
            if (this.photos.length === 0) {
                await this.loadPhotos(1);
            }
            this.swipePhotos = [...this.photos];
            this.swipeIndex = 0;
            this.swipeHistory = [];
            this.swipeSavedCount = 0;
            this.swipeTrashedCount = 0;
            this.resetSwipeCard();
            this.$nextTick(() => {
                if (window.lucide) window.lucide.createIcons();
            });
        },

        resetSwipeCard() {
            this.swipeDeltaX = 0;
            this.swipeDeltaY = 0;
            this.swipeRotateDeg = 0;
            this.swipeCardStatus = '';
            this.swipeIsDragging = false;
            this.isSwipeAnimating = false;
        },

        onTouchStart(e) {
            if (this.isSwipeAnimating) return;
            const touch = e.touches[0];
            this.swipeStartX = touch.clientX;
            this.swipeStartY = touch.clientY;
            this.swipeIsDragging = true;
        },

        onTouchMove(e) {
            if (!this.swipeIsDragging || this.isSwipeAnimating) return;
            const touch = e.touches[0];
            this.onDragMove(touch.clientX, touch.clientY);
        },

        onTouchEnd() {
            if (!this.swipeIsDragging || this.isSwipeAnimating) return;
            this.onDragEnd();
        },

        onMouseDown(e) {
            if (this.isSwipeAnimating) return;
            this.swipeStartX = e.clientX;
            this.swipeStartY = e.clientY;
            this.swipeIsDragging = true;
        },

        onDragMove(clientX, clientY) {
            this.swipeDeltaX = clientX - this.swipeStartX;
            this.swipeDeltaY = (clientY - this.swipeStartY) * 0.4;
            this.swipeRotateDeg = +(this.swipeDeltaX * 0.07).toFixed(1);

            if (this.swipeDeltaX > 50) {
                this.swipeCardStatus = 'save';
            } else if (this.swipeDeltaX < -50) {
                this.swipeCardStatus = 'trash';
            } else {
                this.swipeCardStatus = '';
            }
        },

        onDragEnd() {
            this.swipeIsDragging = false;
            if (this.swipeDeltaX > 110) {
                this.executeSwipeRight();
            } else if (this.swipeDeltaX < -110) {
                this.executeSwipeLeft();
            } else {
                this.isSwipeAnimating = true;
                this.swipeDeltaX = 0;
                this.swipeDeltaY = 0;
                this.swipeRotateDeg = 0;
                this.swipeCardStatus = '';
                setTimeout(() => {
                    this.isSwipeAnimating = false;
                }, 280);
            }
        },

        async executeSwipeRight() {
            if (this.isSwipeAnimating || this.swipeIndex >= this.swipePhotos.length) return;
            const currentPhoto = this.swipePhotos[this.swipeIndex];
            this.isSwipeAnimating = true;
            this.swipeDeltaX = window.innerWidth ? window.innerWidth * 0.8 : 600;
            this.swipeRotateDeg = 25;
            this.swipeCardStatus = 'save';

            try {
                await BingkaiAPI.toggleFavorite(currentPhoto.id);
                currentPhoto.favorite = true;
            } catch (e) {
            }

            this.swipeHistory.push({ photo: currentPhoto, action: 'save' });
            this.swipeSavedCount++;
            this.showToast(`'${currentPhoto.filename}' Disimpan ke Favorit`, 'success');

            setTimeout(() => {
                this.swipeIndex++;
                this.resetSwipeCard();
                this.$nextTick(() => {
                    if (window.lucide) window.lucide.createIcons();
                });
            }, 320);
        },

        async executeSwipeLeft() {
            if (this.isSwipeAnimating || this.swipeIndex >= this.swipePhotos.length) return;
            const currentPhoto = this.swipePhotos[this.swipeIndex];
            this.isSwipeAnimating = true;
            this.swipeDeltaX = window.innerWidth ? -window.innerWidth * 0.8 : -600;
            this.swipeRotateDeg = -25;
            this.swipeCardStatus = 'trash';

            try {
                await BingkaiAPI.moveToTrash(currentPhoto.id);
            } catch (e) {
            }

            this.swipeHistory.push({ photo: currentPhoto, action: 'trash' });
            this.swipeTrashedCount++;
            this.showToast(`'${currentPhoto.filename}' Dipindahkan ke Trash`, 'info');

            setTimeout(() => {
                this.swipeIndex++;
                this.resetSwipeCard();
                this.$nextTick(() => {
                    if (window.lucide) window.lucide.createIcons();
                });
            }, 320);
        },

        executeSwipeSkip() {
            if (this.isSwipeAnimating || this.swipeIndex >= this.swipePhotos.length) return;
            const currentPhoto = this.swipePhotos[this.swipeIndex];
            this.isSwipeAnimating = true;
            this.swipeDeltaY = 400;
            this.swipeRotateDeg = 0;

            this.swipeHistory.push({ photo: currentPhoto, action: 'skip' });

            setTimeout(() => {
                this.swipeIndex++;
                this.resetSwipeCard();
                this.$nextTick(() => {
                    if (window.lucide) window.lucide.createIcons();
                });
            }, 300);
        },

        async undoLastSwipe() {
            if (this.swipeHistory.length === 0 || this.swipeIndex === 0) {
                this.showToast('Belum ada aksi yang dapat di-undo', 'info');
                return;
            }
            const last = this.swipeHistory.pop();
            if (last.action === 'trash') {
                try {
                    await BingkaiAPI.restoreFromTrash(last.photo.id);
                    this.swipeTrashedCount = Math.max(0, this.swipeTrashedCount - 1);
                } catch (e) {
                }
            } else if (last.action === 'save') {
                this.swipeSavedCount = Math.max(0, this.swipeSavedCount - 1);
            }

            this.swipeIndex = Math.max(0, this.swipeIndex - 1);
            this.resetSwipeCard();
            this.showToast(`Membatalkan aksi '${last.photo.filename}'`, 'info');
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
                this.focusedPhotoIndex = 0;
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
                if (this.currentView === 'gallery' || this.currentView === 'favorites') {
                    this.loadPhotos(1);
                }
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
            this.zoomLevel = 1;
            this.rotationDeg = 0;
            this.loadPhotoDetail(photo.id);
            this.$nextTick(() => {
                if (window.lucide) window.lucide.createIcons();
            });
        },

        closeViewer() {
            this.isViewerOpen = false;
            this.activePhoto = null;
            this.photoDetail = null;
            this.isRenameModalOpen = false;
            this.isMoveModalOpen = false;
            this.isAddToAlbumModalOpen = false;
            this.isShortcutsModalOpen = false;
            this.zoomLevel = 1;
            this.rotationDeg = 0;
        },

        zoomIn() {
            if (this.zoomLevel < 3) {
                this.zoomLevel = +(this.zoomLevel + 0.25).toFixed(2);
            }
        },

        zoomOut() {
            if (this.zoomLevel > 0.5) {
                this.zoomLevel = +(this.zoomLevel - 0.25).toFixed(2);
            }
        },

        resetZoom() {
            this.zoomLevel = 1;
            this.rotationDeg = 0;
        },

        rotatePhoto() {
            this.rotationDeg = (this.rotationDeg + 90) % 360;
        },

        copyFilePath(path) {
            if (!path) return;
            navigator.clipboard.writeText(path).then(() => {
                this.showToast('Path file berhasil disalin ke clipboard!', 'success');
            }).catch(() => {
                this.showToast('Gagal menyalin path.', 'error');
            });
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
                this.zoomLevel = 1;
                this.rotationDeg = 0;
                this.loadPhotoDetail(this.activePhoto.id);
            }
        },

        prevPhoto() {
            if (this.activePhotoIndex > 0) {
                this.activePhotoIndex--;
                this.activePhoto = this.photos[this.activePhotoIndex];
                this.zoomLevel = 1;
                this.rotationDeg = 0;
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
                this.showToast(updated.favorite ? 'Ditambahkan ke Favorit' : 'Dihapus dari Favorit', 'info');
            } catch (err) {
                this.showToast(err.message, 'error');
            }
        },

        openRenameModal() {
            if (!this.activePhoto) return;
            this.renameInputName = this.activePhoto.filename;
            this.isRenameModalOpen = true;
        },

        async submitRename() {
            if (!this.activePhoto || !this.renameInputName.trim()) return;
            this.isRenaming = true;
            try {
                const updated = await BingkaiAPI.renamePhoto(this.activePhoto.id, this.renameInputName.trim());
                this.activePhoto.filename = updated.filename;
                if (this.photoDetail) {
                    this.photoDetail.filename = updated.filename;
                    this.photoDetail.file_path = updated.file_path;
                }
                const idx = this.photos.findIndex(p => p.id === updated.id);
                if (idx !== -1) {
                    this.photos[idx].filename = updated.filename;
                }
                this.isRenameModalOpen = false;
                this.showToast('Nama file berhasil diubah!', 'success');
            } catch (err) {
                this.showToast(err.message, 'error');
            } finally {
                this.isRenaming = false;
            }
        },

        openMoveModal() {
            if (!this.activePhoto) return;
            this.targetMoveFolderId = this.folders.length > 0 ? this.folders[0].id : null;
            this.isMoveModalOpen = true;
        },

        async submitMove() {
            if (!this.activePhoto || !this.targetMoveFolderId) {
                this.showToast('Pilih folder tujuan terlebih dahulu.', 'error');
                return;
            }
            this.isMoving = true;
            try {
                const updated = await BingkaiAPI.movePhoto(this.activePhoto.id, this.targetMoveFolderId);
                this.activePhoto.folder_id = updated.folder_id;
                this.activePhoto.folder_path = updated.folder_path;
                if (this.photoDetail) {
                    this.photoDetail.folder_id = updated.folder_id;
                    this.photoDetail.folder_path = updated.folder_path;
                    this.photoDetail.file_path = updated.file_path;
                }
                this.isMoveModalOpen = false;
                this.showToast('Foto berhasil dipindahkan ke folder baru!', 'success');
                await Promise.all([this.loadFolders(), this.loadPhotos(this.page)]);
            } catch (err) {
                this.showToast(err.message, 'error');
            } finally {
                this.isMoving = false;
            }
        },

        async trashActivePhoto() {
            if (!this.activePhoto) return;
            if (!confirm(`Pindahkan foto "${this.activePhoto.filename}" ke Trash (Tong Sampah)?`)) return;
            try {
                await BingkaiAPI.moveToTrash(this.activePhoto.id);
                this.showToast('Foto dipindahkan ke Trash', 'info');
                this.closeViewer();
                await Promise.all([this.loadFolders(), this.loadPhotos(this.page)]);
            } catch (err) {
                this.showToast(err.message, 'error');
            }
        },

        async loadTrash(targetPage = 1) {
            this.isLoadingTrash = true;
            try {
                const result = await BingkaiAPI.getTrash({ page: targetPage, limit: this.limit });
                this.trashPhotos = result.items;
                this.trashTotal = result.total;
                this.trashPage = result.page;
                this.trashTotalPages = result.total_pages;
            } catch (err) {
                this.showToast(err.message || 'Gagal memuat isi trash.', 'error');
            } finally {
                this.isLoadingTrash = false;
                this.$nextTick(() => {
                    if (window.lucide) window.lucide.createIcons();
                });
            }
        },

        async restoreTrashItem(photo) {
            try {
                await BingkaiAPI.restoreFromTrash(photo.id);
                this.showToast(`Foto '${photo.filename}' berhasil dipulihkan!`, 'success');
                await Promise.all([this.loadTrash(this.trashPage), this.loadFolders()]);
            } catch (err) {
                this.showToast(err.message, 'error');
            }
        },

        async deleteTrashItemPermanent(photo) {
            if (!confirm(`Hapus permanen foto "${photo.filename}" dari harddisk PC?\n\nTindakan ini TIDAK DAPAT dibatalkan.`)) return;
            try {
                await BingkaiAPI.deletePermanently(photo.id);
                this.showToast('Foto berhasil dihapus permanen.', 'info');
                await this.loadTrash(this.trashPage);
            } catch (err) {
                this.showToast(err.message, 'error');
            }
        },

        async confirmEmptyTrash() {
            if (!confirm('Kosongkan semua isi Trash secara permanen dari komputer Anda?')) return;
            try {
                const res = await BingkaiAPI.emptyTrash();
                this.showToast(res.message, 'success');
                await this.loadTrash(1);
            } catch (err) {
                this.showToast(err.message, 'error');
            }
        },

        async loadAlbums() {
            this.isLoadingAlbums = true;
            try {
                this.albums = await BingkaiAPI.getAlbums();
            } catch (err) {
                this.showToast(err.message || 'Gagal mengambil daftar album.', 'error');
            } finally {
                this.isLoadingAlbums = false;
            }
        },

        async submitNewAlbum() {
            if (!this.newAlbumName.trim()) {
                this.showToast('Nama album tidak boleh kosong.', 'error');
                return;
            }
            this.isSubmittingAlbum = true;
            try {
                const alb = await BingkaiAPI.createAlbum(this.newAlbumName.trim(), this.newAlbumDesc.trim() || null);
                this.showToast(`Album '${alb.name}' berhasil dibuat!`, 'success');
                this.newAlbumName = '';
                this.newAlbumDesc = '';
                this.isCreateAlbumModalOpen = false;
                await this.loadAlbums();
            } catch (err) {
                this.showToast(err.message, 'error');
            } finally {
                this.isSubmittingAlbum = false;
            }
        },

        async openAlbumDetail(albumId) {
            try {
                this.activeAlbum = await BingkaiAPI.getAlbumDetail(albumId);
                this.currentView = 'albumDetail';
                this.$nextTick(() => {
                    if (window.lucide) window.lucide.createIcons();
                });
            } catch (err) {
                this.showToast(err.message, 'error');
            }
        },

        async deleteAlbum(album) {
            if (!confirm(`Hapus album virtual "${album.name}"?\n(Foto fisik di komputer Anda tidak akan terhapus).`)) return;
            try {
                await BingkaiAPI.deleteAlbum(album.id);
                this.showToast(`Album "${album.name}" dihapus.`, 'info');
                if (this.currentView === 'albumDetail') {
                    this.currentView = 'albums';
                }
                await this.loadAlbums();
            } catch (err) {
                this.showToast(err.message, 'error');
            }
        },

        async addActivePhotoToAlbum(albumId) {
            if (!this.activePhoto) return;
            try {
                const res = await BingkaiAPI.addPhotoToAlbum(albumId, this.activePhoto.id);
                this.showToast(res.message, 'success');
                this.isAddToAlbumModalOpen = false;
                await this.loadAlbums();
            } catch (err) {
                this.showToast(err.message, 'error');
            }
        },

        async removePhotoFromActiveAlbum(photoId) {
            if (!this.activeAlbum) return;
            try {
                await BingkaiAPI.removePhotoFromAlbum(this.activeAlbum.id, photoId);
                this.activeAlbum.photos = this.activeAlbum.photos.filter(p => p.id !== photoId);
                this.showToast('Foto dikeluarkan dari album.', 'info');
                await this.loadAlbums();
            } catch (err) {
                this.showToast(err.message, 'error');
            }
        },

        async loadDuplicates() {
            this.isLoadingDuplicates = true;
            try {
                this.duplicateGroups = await BingkaiAPI.getDuplicates();
            } catch (err) {
                this.showToast(err.message || 'Gagal memindai duplikat.', 'error');
            } finally {
                this.isLoadingDuplicates = false;
                this.$nextTick(() => {
                    if (window.lucide) window.lucide.createIcons();
                });
            }
        },

        async trashDuplicateItem(photo, group) {
            if (!confirm(`Pindahkan salinan "${photo.filename}" ke Trash?`)) return;
            try {
                await BingkaiAPI.moveToTrash(photo.id);
                this.showToast('Salinan foto dipindahkan ke Trash', 'info');
                group.items = group.items.filter(p => p.id !== photo.id);
                group.count = group.items.length;
                if (group.count <= 1) {
                    this.duplicateGroups = this.duplicateGroups.filter(g => g.hash !== group.hash);
                }
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
                this.generateQrCodes();
            } catch (e) {
                console.error(e);
            }
        },

        generateQrCodes() {
            if (!this.systemInfo || !this.systemInfo.remote_urls) return;
            this.qrCodes = {};
            for (const url of this.systemInfo.remote_urls) {
                try {
                    if (window.BingkaiQR && window.BingkaiQR.generateSvg) {
                        this.qrCodes[url] = window.BingkaiQR.generateSvg(url, 260);
                    }
                } catch (err) {
                    console.error(err);
                }
            }
            if (!this.activeQrUrl && this.systemInfo.remote_urls.length > 0) {
                this.activeQrUrl = this.systemInfo.remote_urls[0];
            }
        },

        openQrModal(url = null) {
            if (url) {
                this.activeQrUrl = url;
            } else if (this.systemInfo && this.systemInfo.remote_urls && this.systemInfo.remote_urls.length > 0) {
                this.activeQrUrl = this.systemInfo.remote_urls[0];
            }
            if (!this.qrCodes[this.activeQrUrl] && this.activeQrUrl) {
                this.generateQrCodes();
            }
            this.isQrModalOpen = true;
            this.$nextTick(() => {
                if (window.lucide) window.lucide.createIcons();
            });
        },

        formatSize(bytes) {
            return GalleryUtils.formatFileSize(bytes);
        },

        formatDate(dateStr) {
            return GalleryUtils.formatDateTime(dateStr);
        },

        formatRatio(width, height) {
            return GalleryUtils.getAspectRatio(width, height);
        },

        getThumbUrl(photoId) {
            return BingkaiAPI.getThumbnailUrl(photoId);
        },

        getOrigUrl(photoId) {
            return BingkaiAPI.getOriginalUrl(photoId);
        }
    }));
});
