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
    }
};

window.GalleryUtils = GalleryUtils;
