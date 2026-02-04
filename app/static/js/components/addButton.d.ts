/**
 * TypeScript definitions for AddButton component
 */

/**
 * Song data structure
 */
export interface SongData {
    id?: string;
    audio_id?: string;
    song_id?: string;
    title: string;
    artist: string;
    album?: string;
    duration?: number;
    genre?: string;
    audio_url?: string;
    file_path?: string;
    metadata?: Record<string, any>;
    [key: string]: any;
}

/**
 * AddButton variant options
 */
export type AddButtonVariant = 'primary' | 'secondary' | 'minimal';

/**
 * AddButton size options
 */
export type AddButtonSize = 'small' | 'medium' | 'large';

/**
 * Component state interface
 */
export interface AddButtonState {
    isLoading: boolean;
    isDisabled: boolean;
    isSuccess: boolean;
    isError: boolean;
    errorMessage: string;
    clickCount: number;
    lastClickTime: number;
}

/**
 * Validation result interface
 */
export interface ValidationResult {
    isValid: boolean;
    message: string;
    errors: string[];
}

/**
 * API response interface
 */
export interface AddButtonApiResponse {
    success: boolean;
    data?: any;
    error?: string;
    message?: string;
}

/**
 * Event detail interfaces
 */
export interface AddButtonEventDetail {
    component: AddButton;
    state: AddButtonState;
}

export interface AddButtonSuccessEventDetail extends AddButtonEventDetail {
    response: AddButtonApiResponse;
}

export interface AddButtonErrorEventDetail extends AddButtonEventDetail {
    error: Error;
}

export interface AddButtonOptimisticUpdateEventDetail extends AddButtonEventDetail {
    songData: SongData;
    playlistId: string;
}

/**
 * Main AddButton options interface
 */
export interface AddButtonOptions {
    // Required props
    playlistId: string;
    songData: SongData;
    
    // Optional configuration
    variant?: AddButtonVariant;
    size?: AddButtonSize;
    disabled?: boolean;
    loading?: boolean;
    showTooltip?: boolean;
    showIcon?: boolean;
    
    // Callback functions
    onSuccess?: (response: AddButtonApiResponse, songData: SongData, playlistId: string) => void;
    onError?: (error: Error, songData: SongData, playlistId: string) => void;
    onStateChange?: (state: AddButtonState) => void;
    onClick?: (event: Event, songData: SongData, playlistId: string) => boolean | void;
    
    // Configuration
    enableValidation?: boolean;
    enableDebouncing?: boolean;
    debounceDelay?: number;
    enableOptimisticUpdates?: boolean;
    
    // Accessibility
    ariaLabel?: string;
    tooltipText?: string;
}

/**
 * AddButton factory options interface
 */
export interface AddButtonFactoryOptions {
    defaultOptions?: Partial<AddButtonOptions>;
    enableGlobalErrorHandling?: boolean;
    enableGlobalSuccessHandling?: boolean;
}

/**
 * Component configuration interface
 */
export interface AddButtonConfig {
    apiEndpoint: string;
    validationRules: Record<string, any>;
    debounceSettings: {
        enabled: boolean;
        delay: number;
    };
    optimisticUpdateSettings: {
        enabled: boolean;
        revertOnError: boolean;
    };
    accessibilitySettings: {
        enableAriaLabels: boolean;
        enableKeyboardNavigation: boolean;
        enableFocusManagement: boolean;
    };
}

/**
 * Event listener interfaces
 */
export interface AddButtonEventMap {
    'addButton:click': Event;
    'addButton:success': CustomEvent<AddButtonSuccessEventDetail>;
    'addButton:error': CustomEvent<AddButtonErrorEventDetail>;
    'addButton:stateChange': CustomEvent<AddButtonEventDetail>;
    'addButton:optimisticUpdate': CustomEvent<AddButtonOptimisticUpdateEventDetail>;
    'addButton:revertOptimisticUpdate': CustomEvent<AddButtonOptimisticUpdateEventDetail>;
}

/**
 * AddButton class declaration
 */
export declare class AddButton {
    constructor(options: AddButtonOptions);
    
    // Core methods
    createElement(): HTMLElement;
    destroy(): void;
    
    // State management
    setState(newState: Partial<AddButtonState>): void;
    getState(): AddButtonState;
    reset(): void;
    
    // Option management
    updateOptions(newOptions: Partial<AddButtonOptions>): void;
    updateSongData(newSongData: SongData): void;
    updatePlaylistId(newPlaylistId: string): void;
    
    // Control methods
    enable(): void;
    disable(): void;
    refresh(): Promise<void>;
    
    // Utility methods
    isLoading(): boolean;
    isDisabled(): boolean;
    wasSuccessful(): boolean;
    hasError(): boolean;
    getErrorMessage(): string;
    getElement(): HTMLElement | null;
    getOptions(): AddButtonOptions;
    
    // Event handling
    addEventListener<K extends keyof AddButtonEventMap>(
        type: K,
        listener: (event: AddButtonEventMap[K]) => void
    ): void;
    removeEventListener<K extends keyof AddButtonEventMap>(
        type: K,
        listener: (event: AddButtonEventMap[K]) => void
    ): void;
    
    // Static validation methods
    static validateSongData(songData: SongData): ValidationResult;
    static validatePlaylistId(playlistId: string): boolean;
    static validateApiEndpoint(endpoint: string): boolean;
}

/**
 * AddButtonFactory class declaration
 */
export declare class AddButtonFactory {
    constructor(options?: AddButtonFactoryOptions);
    
    // Factory methods
    create(options: AddButtonOptions, id?: string): AddButton;
    get(id: string): AddButton | null;
    destroy(id: string): void;
    destroyAll(): void;
    getAll(): Map<string, AddButton>;
    
    // Utility methods
    createBatch(
        configs: Array<{ options: AddButtonOptions; id?: string }>
    ): Map<string, AddButton>;
    
    // Event handling
    addGlobalEventListener<K extends keyof AddButtonEventMap>(
        type: K,
        listener: (event: AddButtonEventMap[K] & { target: AddButtonFactory }) => void
    ): void;
    
    // Configuration
    updateDefaultOptions(options: Partial<AddButtonOptions>): void;
    getDefaultOptions(): Partial<AddButtonOptions>;
}

/**
 * Global instances
 */
declare global {
    interface Window {
        AddButton: typeof AddButton;
        AddButtonFactory: typeof AddButtonFactory;
        addButtonFactory: AddButtonFactory;
    }
}

/**
 * Utility type guards
 */
export declare function isAddButtonInstance(obj: any): obj is AddButton;
export declare function isAddButtonFactoryInstance(obj: any): obj is AddButtonFactory;
export declare function isValidSongData(obj: any): obj is SongData;
export declare function isValidAddButtonOptions(obj: any): obj is AddButtonOptions;

/**
 * Constants
 */
export declare const AddButtonConstants: {
    DEFAULT_DEBOUNCE_DELAY: number;
    DEFAULT_VARIANT: AddButtonVariant;
    DEFAULT_SIZE: AddButtonSize;
    MAX_CLICK_COUNT: number;
    SUCCESS_MESSAGE_DURATION: number;
    ERROR_MESSAGE_DURATION: number;
};

/**
 * API endpoint constants
 */
export declare const AddButtonEndpoints: {
    ADD_TO_PLAYLIST: (playlistId: string) => string;
    CHECK_PLAYLIST_CONTAINS: (playlistId: string, audioId: string) => string;
};

/**
 * CSS class name constants
 */
export declare const AddButtonClassNames: {
    BASE: string;
    VARIANTS: Record<AddButtonVariant, string>;
    SIZES: Record<AddButtonSize, string>;
    STATES: Record<string, string>;
};

/**
 * Accessibility constants
 */
export declare const AddButtonAccessibility: {
    ROLES: {
        BUTTON: string;
        TOOLTIP: string;
    };
    KEYBOARD_SHORTCUTS: {
        ACTIVATE: string[];
        CANCEL: string[];
    };
    ARIA_ATTRIBUTES: string[];
};