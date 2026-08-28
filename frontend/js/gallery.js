const GalleryUtils = {
    formatFileSize(bytes) {
        if (!bytes || bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    },

    formatDateTime(dateStr) {
        if (!dateStr) return '-';
        try {
            const date = new Date(dateStr);
            return date.toLocaleDateString('id-ID', {
                year: 'numeric',
                month: 'long',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            });
        } catch (e) {
            return dateStr;
        }
    },

    getDateGroupTitle(dateStr) {
        if (!dateStr) return 'Tanpa Tanggal';
        const date = new Date(dateStr);
        const today = new Date();
        const yesterday = new Date(today);
        yesterday.setDate(yesterday.getDate() - 1);

        if (date.toDateString() === today.toDateString()) {
            return 'Hari Ini';
        }
        if (date.toDateString() === yesterday.toDateString()) {
            return 'Kemarin';
        }

        if (date.getFullYear() === today.getFullYear()) {
            return date.toLocaleDateString('id-ID', { month: 'long', day: 'numeric' });
        }

        return date.toLocaleDateString('id-ID', { month: 'long', year: 'numeric' });
    },

    groupPhotosByDate(photos) {
        if (!photos || photos.length === 0) return [];
        const groups = {};
        const orderedGroupKeys = [];

        photos.forEach(photo => {
            const dateKey = photo.date_taken || photo.date_created || photo.indexed_at;
            const groupTitle = this.getDateGroupTitle(dateKey);

            if (!groups[groupTitle]) {
                groups[groupTitle] = [];
                orderedGroupKeys.push(groupTitle);
            }
            groups[groupTitle].push(photo);
        });

        return orderedGroupKeys.map(title => ({
            title: title,
            items: groups[title]
        }));
    },

    getAspectRatio(width, height) {
        if (!width || !height) return null;
        const gcd = (a, b) => (b === 0 ? a : gcd(b, a % b));
        const divisor = gcd(width, height);
        const rW = width / divisor;
        const rH = height / divisor;
        if (rW === rH) return '1:1 Persegi';
        if (rW === 16 && rH === 9) return '16:9 Landscape';
        if (rW === 9 && rH === 16) return '9:16 Portrait';
        if (rW === 4 && rH === 3) return '4:3 Standar';
        if (rW === 3 && rH === 4) return '3:4 Portrait';
        if (rW === 3 && rH === 2) return '3:2 Klasik';
        if (rW === 2 && rH === 3) return '2:3 Portrait';
        const ratio = (width / height).toFixed(2);
        return `${rW}:${rH} (${ratio})`;
    }
};

window.GalleryUtils = GalleryUtils;
