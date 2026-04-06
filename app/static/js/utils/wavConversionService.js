/**
 * WAV Conversion Service
 * Handles audio to WAV conversion using KIE API
 */

class WavConversionService {
    constructor() {
        this.apiBaseUrl = 'https://api.kie.ai/api/v1/wav/generate';
        this.maxRetries = 3;
        this.pollInterval = 2000; // 2 seconds
        this.pollTimeout = 300000; // 5 minutes
    }

    /**
     * Get authorization token from a meta tag or environment
     * @returns {string} Authorization token
     */
    getAuthToken() {
        // Try to get from meta tag first
        const metaToken = document.querySelector('meta[name="kie-api-token"]');
        if (metaToken) {
            return metaToken.getAttribute('content');
        }
        
        // Fallback: should be stored in window or fetched from backend
        return window.KIE_API_TOKEN || '';
    }

    /**
     * Check if we have valid KIE API configuration
     * @returns {boolean} True if configured
     */
    isConfigured() {
        return !!this.getAuthToken();
    }

    /**
     * Start WAV conversion job
     * @param {string} taskId - The task/job ID to convert
     * @param {string} audioId - The audio ID to convert
     * @param {string} callbackUrl - Optional callback URL
     * @returns {Promise<Object>} Conversion job response
     */
    async startConversion(taskId, audioId, callbackUrl = null) {
        const token = this.getAuthToken();
        
        if (!token) {
            throw new Error('KIE API token not configured');
        }

        if (!taskId || !audioId) {
            throw new Error('taskId and audioId are required');
        }

        const payload = {
            taskId,
            audioId,
        };

        if (callbackUrl) {
            payload.callBackUrl = callbackUrl;
        }

        try {
            const response = await fetch(this.apiBaseUrl, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(payload)
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(
                    errorData.message || 
                    errorData.error || 
                    `KIE API error: ${response.status}`
                );
            }

            return await response.json();
        } catch (error) {
            console.error('WAV conversion start error:', error);
            throw error;
        }
    }

    /**
     * Poll for conversion status
     * @param {string} jobId - The job ID to poll
     * @returns {Promise<Object>} Job status
     */
    async pollConversionStatus(jobId) {
        const token = this.getAuthToken();
        
        if (!token) {
            throw new Error('KIE API token not configured');
        }

        const statusUrl = `https://api.kie.ai/api/v1/wav/status/${jobId}`;

        try {
            const response = await fetch(statusUrl, {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                throw new Error(`Status check failed: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('WAV conversion status error:', error);
            throw error;
        }
    }

    /**
     * Wait for conversion to complete with polling
     * @param {string} jobId - The job ID to monitor
     * @param {Function} onProgress - Optional progress callback
     * @returns {Promise<Object>} Final job status
     */
    async waitForConversion(jobId, onProgress = null) {
        const startTime = Date.now();

        return new Promise((resolve, reject) => {
            const pollTimer = setInterval(async () => {
                try {
                    const status = await this.pollConversionStatus(jobId);
                    
                    if (onProgress) {
                        onProgress(status);
                    }

                    if (status.status === 'completed' || status.status === 'succeeded') {
                        clearInterval(pollTimer);
                        resolve(status);
                    } else if (status.status === 'failed' || status.status === 'error') {
                        clearInterval(pollTimer);
                        reject(new Error(status.error || 'Conversion failed'));
                    } else if (Date.now() - startTime > this.pollTimeout) {
                        clearInterval(pollTimer);
                        reject(new Error('Conversion polling timeout'));
                    }
                } catch (error) {
                    clearInterval(pollTimer);
                    reject(error);
                }
            }, this.pollInterval);
        });
    }

    /**
     * Get download URL for converted WAV file
     * @param {string} jobId - The job ID
     * @returns {string} Download URL
     */
    getDownloadUrl(jobId) {
        return `https://api.kie.ai/api/v1/wav/download/${jobId}`;
    }

    /**
     * Full conversion flow: start -> wait -> download
     * @param {string} taskId - Task ID
     * @param {string} audioId - Audio ID
     * @param {string} filename - Filename for download (without extension)
     * @param {Function} onProgress - Progress callback
     * @returns {Promise<Blob>} Converted WAV file blob
     */
    async convertToWav(taskId, audioId, filename = 'converted', onProgress = null) {
        try {
            // Start conversion
            if (onProgress) onProgress({ status: 'starting', message: 'Starting conversion...' });
            
            const startResponse = await this.startConversion(taskId, audioId);
            const jobId = startResponse.jobId || startResponse.id;
            
            if (!jobId) {
                throw new Error('No job ID returned from conversion start');
            }

            // Wait for completion
            if (onProgress) onProgress({ status: 'waiting', message: 'Processing conversion...' });
            
            const finalStatus = await this.waitForConversion(jobId, onProgress);

            // Download file
            if (onProgress) onProgress({ status: 'downloading', message: 'Downloading WAV file...' });
            
            const downloadUrl = this.getDownloadUrl(jobId);
            const response = await fetch(downloadUrl);
            
            if (!response.ok) {
                throw new Error(`Download failed: ${response.status}`);
            }

            const blob = await response.blob();
            
            // Trigger download
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `${filename}.wav`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);

            if (onProgress) onProgress({ status: 'completed', message: 'Conversion complete!' });
            
            return blob;
        } catch (error) {
            console.error('Full conversion error:', error);
            if (onProgress) onProgress({ status: 'error', message: error.message });
            throw error;
        }
    }
}

// Create singleton instance
window.WavConversionService = new WavConversionService();
