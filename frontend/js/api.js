const BingkaiAPI = {
    baseUrl: '',

    async request(endpoint, options = {}) {
        const url = `${this.baseUrl}${endpoint}`;
        const defaultHeaders = {
            'Accept': 'application/json',
        };

        if (options.body && typeof options.body === 'object' && !(options.body instanceof FormData)) {
            defaultHeaders['Content-Type'] = 'application/json';
            options.body = JSON.stringify(options.body);
        }

        const config = {
            ...options,
            headers: {
                ...defaultHeaders,
                ...options.headers,
            },
            credentials: 'same-origin',
        };

        try {
            const response = await fetch(url, config);

            if (response.status === 401 && !endpoint.includes('/auth/login')) {
                window.dispatchEvent(new CustomEvent('bingkai-unauthorized'));
                throw new Error('Session telah berakhir. Silakan login kembali.');
            }

            const data = await response.json().catch(() => null);

            if (!response.ok) {
                const errorMessage = (data && data.detail) ? data.detail : `Error ${response.status}: Permintaan gagal diproses.`;
                throw new Error(errorMessage);
            }

            return data;
        } catch (error) {
            console.error(`API Error on [${options.method || 'GET'} ${endpoint}]:`, error);
            throw error;
        }
    },

    async login(username, password) {
        return this.request('/api/auth/login', {
            method: 'POST',
            body: { username, password }
        });
    },

    async logout() {
        return this.request('/api/auth/logout', {
            method: 'POST'
        });
    },

    async getMe() {
        return this.request('/api/auth/me');
    },

    async getFolders() {
        return this.request('/api/folders');
    },

    async addFolder(path, name = null) {
        return this.request('/api/folders', {
            method: 'POST',
            body: { path, name }
        });
    },

    async deleteFolder(folderId) {
        return this.request(`/api/folders/${folderId}`, {
            method: 'DELETE'
        });
    },

    async scanFolder(folderId) {
        return this.request(`/api/folders/${folderId}/scan`, {
            method: 'POST'
        });
    },

    async getPhotos({ page = 1, limit = 50, folderId = null, favorite = false, q = null, sort = 'date_desc' } = {}) {
        const params = new URLSearchParams({
            page: page.toString(),
            limit: limit.toString(),
            sort: sort,
        });

        if (folderId) params.append('folder_id', folderId.toString());
        if (favorite) params.append('favorite', 'true');
        if (q && q.trim()) params.append('q', q.trim());

        return this.request(`/api/photos?${params.toString()}`);
    },

    async getPhotoDetail(photoId) {
        return this.request(`/api/photos/${photoId}`);
    },

    async toggleFavorite(photoId) {
        return this.request(`/api/photos/${photoId}/favorite`, {
            method: 'POST'
        });
    },

    async renamePhoto(photoId, name) {
        return this.request(`/api/photos/${photoId}/rename`, {
            method: 'PATCH',
            body: { name }
        });
    },

    async movePhoto(photoId, targetFolderId) {
        return this.request(`/api/photos/${photoId}/move`, {
            method: 'POST',
            body: { target_folder_id: parseInt(targetFolderId) }
        });
    },

    async moveToTrash(photoId) {
        return this.request(`/api/photos/${photoId}/trash`, {
            method: 'POST'
        });
    },

    async restoreFromTrash(photoId) {
        return this.request(`/api/photos/${photoId}/restore`, {
            method: 'POST'
        });
    },

    async deletePermanently(photoId) {
        return this.request(`/api/photos/${photoId}/permanent`, {
            method: 'DELETE'
        });
    },

    async getTrash({ page = 1, limit = 50 } = {}) {
        return this.request(`/api/trash?page=${page}&limit=${limit}`);
    },

    async emptyTrash() {
        return this.request('/api/trash/empty', {
            method: 'DELETE'
        });
    },

    async getDuplicates() {
        return this.request('/api/duplicates');
    },

    async getAlbums() {
        return this.request('/api/albums');
    },

    async createAlbum(name, description = null) {
        return this.request('/api/albums', {
            method: 'POST',
            body: { name, description }
        });
    },

    async getAlbumDetail(albumId) {
        return this.request(`/api/albums/${albumId}`);
    },

    async deleteAlbum(albumId) {
        return this.request(`/api/albums/${albumId}`, {
            method: 'DELETE'
        });
    },

    async addPhotoToAlbum(albumId, photoId) {
        return this.request(`/api/albums/${albumId}/photos/${photoId}`, {
            method: 'POST'
        });
    },

    async removePhotoFromAlbum(albumId, photoId) {
        return this.request(`/api/albums/${albumId}/photos/${photoId}`, {
            method: 'DELETE'
        });
    },

    getThumbnailUrl(photoId) {
        return `/api/photos/${photoId}/thumbnail`;
    },

    getOriginalUrl(photoId) {
        return `/api/photos/${photoId}/original`;
    },

    async getDashboard() {
        return this.request('/api/dashboard');
    },

    async getSystemInfo() {
        return this.request('/api/system/info');
    }
};

window.BingkaiAPI = BingkaiAPI;
