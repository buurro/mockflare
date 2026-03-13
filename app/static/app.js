// Mockflare Dashboard Application
const app = {
    currentZone: null,
    deleteCallback: null,

    // Initialize the application
    init() {
        // Handle browser back/forward buttons
        window.addEventListener('popstate', (event) => {
            if (event.state?.zoneId) {
                this.openZone(event.state.zoneId, false);
            } else {
                this.showZonesList(false);
            }
        });

        // Check URL on initial load
        const params = new URLSearchParams(window.location.search);
        const zoneId = params.get('zone');
        if (zoneId) {
            // Replace current state so back works correctly
            history.replaceState({ zoneId }, '', `/?zone=${zoneId}`);
            this.openZone(zoneId, false);
        } else {
            history.replaceState({}, '', '/');
            this.loadZones();
        }
    },

    // API Helper
    async api(endpoint, options = {}) {
        const url = endpoint;
        const config = {
            headers: {
                'Content-Type': 'application/json',
            },
            ...options,
        };

        if (config.body && typeof config.body === 'object') {
            config.body = JSON.stringify(config.body);
        }

        try {
            const response = await fetch(url, config);
            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || 'An error occurred');
            }

            return data;
        } catch (error) {
            this.showToast(error.message, 'error');
            throw error;
        }
    },

    // Toast Notifications
    showToast(message, type = 'success') {
        const container = document.getElementById('toast-container');
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.textContent = message;
        container.appendChild(toast);

        setTimeout(() => {
            toast.remove();
        }, 3000);
    },

    // Modal Management
    openModal(modalId) {
        document.getElementById(modalId).classList.add('active');
    },

    closeModal(modalId) {
        document.getElementById(modalId).classList.remove('active');
    },

    // View Management
    showZonesList(pushState = true) {
        document.getElementById('zones-view').style.display = 'block';
        document.getElementById('zone-detail-view').style.display = 'none';
        document.getElementById('breadcrumb').innerHTML = '';
        this.currentZone = null;

        if (pushState) {
            history.pushState({}, '', '/');
        }

        document.title = 'Mockflare Dashboard';
        this.loadZones();
    },

    showZoneDetail(zone, pushState = true) {
        this.currentZone = zone;
        document.getElementById('zones-view').style.display = 'none';
        document.getElementById('zone-detail-view').style.display = 'block';
        document.getElementById('zone-detail-title').textContent = zone.name;
        document.getElementById('breadcrumb').innerHTML = `
            <a href="#" onclick="app.showZonesList(); return false;">Zones</a>
            <span class="separator">/</span>
            <span class="current">${zone.name}</span>
        `;

        if (pushState) {
            history.pushState({ zoneId: zone.id }, '', `/?zone=${zone.id}`);
        }

        document.title = `${zone.name} - Mockflare`;
        this.switchTab('dns-records');
        this.loadDnsRecords();
        this.loadCustomHostnames();
    },

    switchTab(tabName) {
        // Update tab buttons
        document.querySelectorAll('.tab').forEach(tab => {
            tab.classList.toggle('active', tab.dataset.tab === tabName);
        });

        // Update tab content
        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.toggle('active', content.id === `${tabName}-tab`);
        });
    },

    // Status Badge Helper
    getStatusBadge(status) {
        const statusLower = status.toLowerCase();
        let badgeClass = 'badge-default';

        if (statusLower === 'active') {
            badgeClass = 'badge-active';
        } else if (statusLower.includes('pending') || statusLower === 'initializing') {
            badgeClass = 'badge-pending';
        } else if (statusLower.includes('deleted') || statusLower.includes('blocked') || statusLower.includes('failed')) {
            badgeClass = 'badge-inactive';
        }

        return `<span class="badge ${badgeClass}">${status}</span>`;
    },

    // Format DNS record name for display
    formatRecordName(name, zoneName) {
        if (name === zoneName) {
            return `<span class="record-name"><span class="subdomain">@</span><span class="domain">.${zoneName}</span></span>`;
        }
        if (name.endsWith('.' + zoneName)) {
            const subdomain = name.slice(0, -(zoneName.length + 1));
            return `<span class="record-name"><span class="subdomain">${subdomain}</span><span class="domain">.${zoneName}</span></span>`;
        }
        return `<span class="record-name"><span class="subdomain">${name}</span></span>`;
    },

    // Convert subdomain input to full domain name
    subdomainToFullName(input, zoneName) {
        const trimmed = input.trim();
        if (trimmed === '@' || trimmed === '') {
            return zoneName;
        }
        // If it already ends with the zone name, use as-is
        if (trimmed.endsWith('.' + zoneName) || trimmed === zoneName) {
            return trimmed;
        }
        // Otherwise, append zone name
        return `${trimmed}.${zoneName}`;
    },

    // Convert full domain name to subdomain for editing
    fullNameToSubdomain(fullName, zoneName) {
        if (fullName === zoneName) {
            return '@';
        }
        if (fullName.endsWith('.' + zoneName)) {
            return fullName.slice(0, -(zoneName.length + 1));
        }
        return fullName;
    },

    // Update content hints based on record type
    updateRecordTypeHints() {
        const type = document.getElementById('dns-record-type').value;
        const contentInput = document.getElementById('dns-record-content');
        const contentHint = document.getElementById('dns-record-content-hint');

        const hints = {
            'A': { placeholder: '192.0.2.1', hint: 'IPv4 address' },
            'AAAA': { placeholder: '2001:db8::1', hint: 'IPv6 address' },
            'CNAME': { placeholder: 'target.example.com', hint: 'Target hostname (cannot be used on root domain)' },
            'MX': { placeholder: 'mail.example.com', hint: 'Mail server hostname' },
            'TXT': { placeholder: 'v=spf1 include:_spf.example.com ~all', hint: 'Text content (SPF, DKIM, verification, etc.)' },
            'NS': { placeholder: 'ns1.example.com', hint: 'Nameserver hostname' },
            'PTR': { placeholder: 'hostname.example.com', hint: 'Pointer to a hostname' },
            'SRV': { placeholder: '10 5 5060 sipserver.example.com', hint: 'Format: priority weight port target' },
            'CAA': { placeholder: '0 issue "letsencrypt.org"', hint: 'Certificate Authority Authorization' },
        };

        const config = hints[type] || { placeholder: '', hint: 'Record content' };
        contentInput.placeholder = config.placeholder;
        contentHint.textContent = config.hint;
    },

    // === ZONES ===
    async loadZones() {
        try {
            const data = await this.api('/zones');
            const zones = data.result || [];
            const tbody = document.getElementById('zones-table-body');
            const emptyState = document.getElementById('zones-empty');
            const tableContainer = document.querySelector('#zones-view .table-container');

            if (zones.length === 0) {
                tbody.innerHTML = '';
                emptyState.style.display = 'block';
                tableContainer.style.display = 'none';
                return;
            }

            emptyState.style.display = 'none';
            tableContainer.style.display = 'block';
            tbody.innerHTML = zones.map(zone => `
                <tr>
                    <td>
                        <a href="#" class="zone-link" onclick="app.openZone('${zone.id}'); return false;">
                            ${zone.name}
                        </a>
                    </td>
                    <td>${this.getStatusBadge(zone.status)}</td>
                    <td><span class="badge badge-default">${zone.type}</span></td>
                    <td><span class="mono">${zone.account_id}</span></td>
                    <td class="actions">
                        <button class="btn btn-sm btn-secondary" onclick="app.editZone('${zone.id}')">Edit</button>
                        <button class="btn btn-sm btn-danger" onclick="app.confirmDeleteZone('${zone.id}', '${zone.name}')">Delete</button>
                    </td>
                </tr>
            `).join('');
        } catch (error) {
            console.error('Failed to load zones:', error);
        }
    },

    async openZone(zoneId, pushState = true) {
        try {
            const data = await this.api(`/zones/${zoneId}`);
            this.showZoneDetail(data.result, pushState);
        } catch (error) {
            console.error('Failed to load zone:', error);
            // If zone not found, go back to list
            this.showZonesList(pushState);
        }
    },

    showZoneModal(zone = null) {
        const isEdit = zone !== null;
        document.getElementById('zone-modal-title').textContent = isEdit ? 'Edit Zone' : 'Add Zone';
        document.getElementById('zone-id').value = isEdit ? zone.id : '';
        document.getElementById('zone-name').value = isEdit ? zone.name : '';
        document.getElementById('zone-name').disabled = isEdit;
        document.getElementById('zone-account-id').value = isEdit ? zone.account_id : '';
        document.getElementById('zone-account-id').disabled = isEdit;
        document.getElementById('zone-type').value = isEdit ? zone.type : 'full';
        this.openModal('zone-modal');
    },

    async editZone(zoneId) {
        try {
            const data = await this.api(`/zones/${zoneId}`);
            this.showZoneModal(data.result);
        } catch (error) {
            console.error('Failed to load zone for editing:', error);
        }
    },

    async saveZone(event) {
        event.preventDefault();
        const zoneId = document.getElementById('zone-id').value;
        const isEdit = zoneId !== '';

        const payload = {
            type: document.getElementById('zone-type').value,
        };

        if (!isEdit) {
            payload.name = document.getElementById('zone-name').value;
            payload.account_id = document.getElementById('zone-account-id').value;
        }

        try {
            if (isEdit) {
                await this.api(`/zones/${zoneId}`, {
                    method: 'PATCH',
                    body: payload,
                });
                this.showToast('Zone updated successfully');
            } else {
                await this.api('/zones', {
                    method: 'POST',
                    body: payload,
                });
                this.showToast('Zone created successfully');
            }
            this.closeModal('zone-modal');
            this.loadZones();
        } catch (error) {
            console.error('Failed to save zone:', error);
        }
    },

    confirmDeleteZone(zoneId, zoneName) {
        document.getElementById('delete-message').textContent =
            `Are you sure you want to delete the zone "${zoneName}"? This will also delete all DNS records and custom hostnames.`;
        document.getElementById('delete-confirm-btn').onclick = () => this.deleteZone(zoneId);
        this.openModal('delete-modal');
    },

    async deleteZone(zoneId) {
        try {
            await this.api(`/zones/${zoneId}`, { method: 'DELETE' });
            this.showToast('Zone deleted successfully');
            this.closeModal('delete-modal');
            this.loadZones();
        } catch (error) {
            console.error('Failed to delete zone:', error);
        }
    },

    // === DNS RECORDS ===
    async loadDnsRecords() {
        if (!this.currentZone) return;

        try {
            const data = await this.api(`/zones/${this.currentZone.id}/dns_records`);
            const records = data.result || [];
            const tbody = document.getElementById('dns-records-table-body');
            const emptyState = document.getElementById('dns-records-empty');
            const tableContainer = document.querySelector('#dns-records-tab .table-container');

            if (records.length === 0) {
                tbody.innerHTML = '';
                emptyState.style.display = 'block';
                tableContainer.style.display = 'none';
                return;
            }

            emptyState.style.display = 'none';
            tableContainer.style.display = 'block';
            tbody.innerHTML = records.map(record => `
                <tr>
                    <td>${this.formatRecordName(record.name, this.currentZone.name)}</td>
                    <td><span class="badge badge-type">${record.type}</span></td>
                    <td><span class="mono truncate" title="${this.escapeHtml(record.content)}">${this.escapeHtml(record.content)}</span></td>
                    <td>${record.ttl === 1 ? 'Auto' : this.formatTTL(record.ttl)}</td>
                    <td>
                        <span class="proxied-badge ${record.proxied ? 'on' : 'off'}">
                            ${record.proxied ? 'Proxied' : 'DNS only'}
                        </span>
                    </td>
                    <td class="actions">
                        <button class="btn btn-sm btn-secondary" onclick="app.editDnsRecord('${record.id}')">Edit</button>
                        <button class="btn btn-sm btn-danger" onclick="app.confirmDeleteDnsRecord('${record.id}', '${this.escapeHtml(record.name)}')">Delete</button>
                    </td>
                </tr>
            `).join('');
        } catch (error) {
            console.error('Failed to load DNS records:', error);
        }
    },

    formatTTL(seconds) {
        if (seconds < 60) return `${seconds}s`;
        if (seconds < 3600) return `${Math.floor(seconds / 60)}m`;
        if (seconds < 86400) return `${Math.floor(seconds / 3600)}h`;
        return `${Math.floor(seconds / 86400)}d`;
    },

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    },

    showDnsRecordModal(record = null) {
        const isEdit = record !== null;
        document.getElementById('dns-record-modal-title').textContent = isEdit ? 'Edit DNS Record' : 'Add DNS Record';
        document.getElementById('dns-record-id').value = isEdit ? record.id : '';

        // Update zone suffix display
        const zoneName = this.currentZone?.name || 'example.com';
        document.getElementById('dns-record-zone-suffix').textContent = '.' + zoneName;

        // Convert full name to subdomain for editing
        const nameValue = isEdit ? this.fullNameToSubdomain(record.name, zoneName) : '';
        document.getElementById('dns-record-name').value = nameValue;

        document.getElementById('dns-record-type').value = isEdit ? record.type : 'A';
        document.getElementById('dns-record-content').value = isEdit ? record.content : '';
        document.getElementById('dns-record-ttl').value = isEdit ? record.ttl : 1;
        document.getElementById('dns-record-proxied').checked = isEdit ? record.proxied : false;
        document.getElementById('dns-record-comment').value = isEdit ? (record.comment || '') : '';

        this.updateRecordTypeHints();
        this.openModal('dns-record-modal');
    },

    async editDnsRecord(recordId) {
        try {
            const data = await this.api(`/zones/${this.currentZone.id}/dns_records/${recordId}`);
            this.showDnsRecordModal(data.result);
        } catch (error) {
            console.error('Failed to load DNS record for editing:', error);
        }
    },

    async saveDnsRecord(event) {
        event.preventDefault();
        const recordId = document.getElementById('dns-record-id').value;
        const isEdit = recordId !== '';

        // Convert subdomain to full name
        const nameInput = document.getElementById('dns-record-name').value;
        const fullName = this.subdomainToFullName(nameInput, this.currentZone.name);

        const payload = {
            name: fullName,
            type: document.getElementById('dns-record-type').value,
            content: document.getElementById('dns-record-content').value,
            ttl: parseInt(document.getElementById('dns-record-ttl').value, 10),
            proxied: document.getElementById('dns-record-proxied').checked,
            comment: document.getElementById('dns-record-comment').value || null,
        };

        try {
            if (isEdit) {
                await this.api(`/zones/${this.currentZone.id}/dns_records/${recordId}`, {
                    method: 'PATCH',
                    body: payload,
                });
                this.showToast('DNS record updated successfully');
            } else {
                await this.api(`/zones/${this.currentZone.id}/dns_records`, {
                    method: 'POST',
                    body: payload,
                });
                this.showToast('DNS record created successfully');
            }
            this.closeModal('dns-record-modal');
            this.loadDnsRecords();
        } catch (error) {
            console.error('Failed to save DNS record:', error);
        }
    },

    confirmDeleteDnsRecord(recordId, recordName) {
        document.getElementById('delete-message').textContent =
            `Are you sure you want to delete the DNS record "${recordName}"?`;
        document.getElementById('delete-confirm-btn').onclick = () => this.deleteDnsRecord(recordId);
        this.openModal('delete-modal');
    },

    async deleteDnsRecord(recordId) {
        try {
            await this.api(`/zones/${this.currentZone.id}/dns_records/${recordId}`, { method: 'DELETE' });
            this.showToast('DNS record deleted successfully');
            this.closeModal('delete-modal');
            this.loadDnsRecords();
        } catch (error) {
            console.error('Failed to delete DNS record:', error);
        }
    },

    async addNsRecords() {
        if (!this.currentZone) return;

        const nameServers = this.currentZone.name_servers || [];
        if (nameServers.length === 0) {
            this.showToast('No nameservers configured for this zone', 'error');
            return;
        }

        try {
            let created = 0;
            for (const ns of nameServers) {
                await this.api(`/zones/${this.currentZone.id}/dns_records`, {
                    method: 'POST',
                    body: {
                        name: this.currentZone.name,
                        type: 'NS',
                        content: ns,
                        ttl: 86400,
                        proxied: false,
                        comment: 'Zone nameserver',
                    },
                });
                created++;
            }
            this.showToast(`Added ${created} NS record${created !== 1 ? 's' : ''}`);
            this.loadDnsRecords();
        } catch (error) {
            console.error('Failed to add NS records:', error);
        }
    },

    // === CUSTOM HOSTNAMES ===
    async loadCustomHostnames() {
        if (!this.currentZone) return;

        try {
            const data = await this.api(`/zones/${this.currentZone.id}/custom_hostnames`);
            const hostnames = data.result || [];
            const tbody = document.getElementById('custom-hostnames-table-body');
            const emptyState = document.getElementById('custom-hostnames-empty');
            const tableContainer = document.querySelector('#custom-hostnames-tab .table-container');

            if (hostnames.length === 0) {
                tbody.innerHTML = '';
                emptyState.style.display = 'block';
                tableContainer.style.display = 'none';
                return;
            }

            emptyState.style.display = 'none';
            tableContainer.style.display = 'block';
            tbody.innerHTML = hostnames.map(hostname => `
                <tr>
                    <td><span class="mono">${hostname.hostname}</span></td>
                    <td>${this.getStatusBadge(hostname.status)}</td>
                    <td>${this.getStatusBadge(hostname.ssl.status)}</td>
                    <td><span class="mono">${hostname.custom_origin_server || '—'}</span></td>
                    <td class="actions">
                        <button class="btn btn-sm btn-secondary" onclick="app.editCustomHostname('${hostname.id}')">Edit</button>
                        <button class="btn btn-sm btn-danger" onclick="app.confirmDeleteCustomHostname('${hostname.id}', '${hostname.hostname}')">Delete</button>
                    </td>
                </tr>
            `).join('');
        } catch (error) {
            console.error('Failed to load custom hostnames:', error);
        }
    },

    showCustomHostnameModal(hostname = null) {
        const isEdit = hostname !== null;
        document.getElementById('custom-hostname-modal-title').textContent = isEdit ? 'Edit Custom Hostname' : 'Add Custom Hostname';
        document.getElementById('custom-hostname-id').value = isEdit ? hostname.id : '';
        document.getElementById('custom-hostname-hostname').value = isEdit ? hostname.hostname : '';
        document.getElementById('custom-hostname-hostname').disabled = isEdit;
        document.getElementById('custom-hostname-ssl-method').value = isEdit ? hostname.ssl.method : 'http';
        document.getElementById('custom-hostname-origin').value = isEdit ? (hostname.custom_origin_server || '') : '';
        document.getElementById('custom-hostname-sni').value = isEdit ? (hostname.custom_origin_sni || '') : '';
        this.openModal('custom-hostname-modal');
    },

    async editCustomHostname(hostnameId) {
        try {
            const data = await this.api(`/zones/${this.currentZone.id}/custom_hostnames/${hostnameId}`);
            this.showCustomHostnameModal(data.result);
        } catch (error) {
            console.error('Failed to load custom hostname for editing:', error);
        }
    },

    async saveCustomHostname(event) {
        event.preventDefault();
        const hostnameId = document.getElementById('custom-hostname-id').value;
        const isEdit = hostnameId !== '';

        const payload = {
            ssl: {
                method: document.getElementById('custom-hostname-ssl-method').value,
            },
            custom_origin_server: document.getElementById('custom-hostname-origin').value || null,
            custom_origin_sni: document.getElementById('custom-hostname-sni').value || null,
        };

        if (!isEdit) {
            payload.hostname = document.getElementById('custom-hostname-hostname').value;
        }

        try {
            if (isEdit) {
                await this.api(`/zones/${this.currentZone.id}/custom_hostnames/${hostnameId}`, {
                    method: 'PATCH',
                    body: payload,
                });
                this.showToast('Custom hostname updated successfully');
            } else {
                await this.api(`/zones/${this.currentZone.id}/custom_hostnames`, {
                    method: 'POST',
                    body: payload,
                });
                this.showToast('Custom hostname created successfully');
            }
            this.closeModal('custom-hostname-modal');
            this.loadCustomHostnames();
        } catch (error) {
            console.error('Failed to save custom hostname:', error);
        }
    },

    confirmDeleteCustomHostname(hostnameId, hostname) {
        document.getElementById('delete-message').textContent =
            `Are you sure you want to delete the custom hostname "${hostname}"?`;
        document.getElementById('delete-confirm-btn').onclick = () => this.deleteCustomHostname(hostnameId);
        this.openModal('delete-modal');
    },

    async deleteCustomHostname(hostnameId) {
        try {
            await this.api(`/zones/${this.currentZone.id}/custom_hostnames/${hostnameId}`, { method: 'DELETE' });
            this.showToast('Custom hostname deleted successfully');
            this.closeModal('delete-modal');
            this.loadCustomHostnames();
        } catch (error) {
            console.error('Failed to delete custom hostname:', error);
        }
    },
};

// Initialize the app when the DOM is ready
document.addEventListener('DOMContentLoaded', () => app.init());
