# One-Click Template Application Design

## Overview
The one-click template application feature allows users to instantly apply template prompts, styles, and settings to the music generation form with a single click. This dramatically reduces the time and effort required to create high-quality music prompts.

## 1. Integration Architecture

### Data Flow
```
Template Gallery → Template Selection → Form Population → Generation Ready
      ↓                   ↓                   ↓               ↓
Display templates → User clicks template → Auto-fill form → Ready to generate
```

### Components Involved
1. **Template Gallery Component** - Displays templates and handles selection
2. **Form Manager Component** - Manages the prompt form state
3. **Notification System** - Provides user feedback
4. **Template Service** - Handles template data and application logic

## 2. Template Application Process

### Step-by-Step Flow
1. **User Interaction**: User clicks "Use This Template" button or template card
2. **Template Retrieval**: System fetches complete template data (prompt, style, settings)
3. **Form Population**: Template data is applied to the appropriate form fields
4. **UI Feedback**: Visual feedback shows template has been applied
5. **State Update**: Form validation and character counters are updated
6. **Ready State**: Generate button becomes active (if audio source is selected)

## 3. Form Field Mapping

### Template Data → Form Fields Mapping
| Template Field | Form Field | Element ID (from index.html) | Notes |
|----------------|------------|------------------------------|-------|
| `prompt` | Prompt Textarea | `promptInput` (line 187) | Main prompt text |
| `style` | Style Input | `styleInput` (line 100) | Style/tags field |
| `instrumental` | Instrumental Toggle | `instrumentalToggle` (line 105) | Checkbox state |
| `metadata.model` | Model Select | `modelSelect` (line 95) | AI model selection |
| `tags` | Quick Tags | N/A | Could populate tag buttons |
| `bpm` | BPM Display | N/A | Could show in UI (future) |
| `duration` | Duration Display | N/A | Could show in UI (future) |

## 4. JavaScript Implementation

### File: `app/static/js/components/templateApplier.js`
```javascript
/**
 * Template Applier component for applying templates to the music generation form.
 */
class TemplateApplier {
  constructor() {
    // Form element references (will be initialized)
    this.promptInput = null;
    this.styleInput = null;
    this.instrumentalToggle = null;
    this.modelSelect = null;
    this.promptChars = null;
    this.styleChars = null;
    this.titleInput = null;
    this.titleChars = null;
  }
  
  /**
   * Initialize the template applier.
   * @param {Object} formElements - Form element references
   */
  initialize(formElements) {
    this.promptInput = formElements.promptInput;
    this.styleInput = formElements.styleInput;
    this.instrumentalToggle = formElements.instrumentalToggle;
    this.modelSelect = formElements.modelSelect;
    this.promptChars = formElements.promptChars;
    this.styleChars = formElements.styleChars;
    this.titleInput = formElements.titleInput;
    this.titleChars = formElements.titleChars;
    
    // Listen for template application events
    document.addEventListener('templateApplied', (event) => {
      this.applyTemplate(event.detail.template);
    });
  }
  
  /**
   * Apply a template to the form.
   * @param {Object} template - Template data object
   */
  applyTemplate(template) {
    console.log('Applying template:', template.name);
    
    // Apply prompt text
    if (template.prompt && this.promptInput) {
      this.promptInput.value = template.prompt;
      this.updateCharacterCounter(this.promptInput, this.promptChars);
    }
    
    // Apply style/tags
    if (template.style && this.styleInput) {
      this.styleInput.value = template.style;
      this.updateCharacterCounter(this.styleInput, this.styleChars);
    }
    
    // Apply instrumental setting
    if (this.instrumentalToggle) {
      const isInstrumental = template.instrumental !== false; // Default to true
      this.instrumentalToggle.checked = isInstrumental;
      
      // Trigger change event for any listeners
      this.instrumentalToggle.dispatchEvent(new Event('change'));
    }
    
    // Apply model selection
    if (template.metadata?.model && this.modelSelect) {
      this.modelSelect.value = template.metadata.model;
    }
    
    // Apply title if available (optional)
    if (template.name && this.titleInput) {
      this.titleInput.value = template.name;
      this.updateCharacterCounter(this.titleInput, this.titleChars);
    }
    
    // Focus on the prompt input for immediate editing
    if (this.promptInput) {
      this.promptInput.focus();
      // Move cursor to end of text
      this.promptInput.setSelectionRange(
        this.promptInput.value.length,
        this.promptInput.value.length
      );
    }
    
    // Update form validation state
    this.updateFormValidation();
    
    // Show visual feedback
    this.showApplicationFeedback(template);
  }
  
  /**
   * Update character counter for a text input.
   * @param {HTMLInputElement|HTMLTextAreaElement} input - Input element
   * @param {HTMLElement} counterElement - Character counter element
   */
  updateCharacterCounter(input, counterElement) {
    if (!input || !counterElement) return;
    
    const currentLength = input.value.length;
    const maxLength = parseInt(input.getAttribute('maxlength')) || 200;
    
    counterElement.textContent = `${currentLength}/${maxLength}`;
    
    // Update color based on length
    const percentage = (currentLength / maxLength) * 100;
    if (percentage > 90) {
      counterElement.classList.add('text-red-500');
      counterElement.classList.remove('text-slate-500');
    } else if (percentage > 75) {
      counterElement.classList.add('text-amber-500');
      counterElement.classList.remove('text-slate-500');
    } else {
      counterElement.classList.remove('text-red-500', 'text-amber-500');
      counterElement.classList.add('text-slate-500');
    }
  }
  
  /**
   * Update form validation state.
   */
  updateFormValidation() {
    // Check if form is valid for generation
    const hasPrompt = this.promptInput && this.promptInput.value.trim().length > 0;
    const hasAudioSource = this.checkAudioSource(); // Would check with fileHandler
    
    // Update generate button state if available
    const generateBtn = document.getElementById('generateBtn');
    if (generateBtn) {
      generateBtn.disabled = !(hasPrompt && hasAudioSource);
    }
    
    // Dispatch event for other components
    document.dispatchEvent(new CustomEvent('formUpdated', {
      detail: { hasValidPrompt: hasPrompt }
    }));
  }
  
  /**
   * Check if audio source is selected.
   * @returns {boolean} True if audio source is selected
   */
  checkAudioSource() {
    // This would integrate with the existing fileHandler component
    // For now, return true to allow generation
    return true;
  }
  
  /**
   * Show visual feedback for template application.
   * @param {Object} template - Applied template
   */
  showApplicationFeedback(template) {
    // 1. Show notification
    this.showNotification(`"${template.name}" template applied! Ready to generate.`);
    
    // 2. Highlight the form section briefly
    this.highlightFormSection();
    
    // 3. Update any template-specific UI indicators
    this.updateTemplateIndicators(template);
  }
  
  /**
   * Show application notification.
   * @param {string} message - Notification message
   */
  showNotification(message) {
    // Use existing notification system if available
    if (window.notificationSystem) {
      window.notificationSystem.showSuccess(message);
    } else {
      // Fallback notification
      const notification = document.createElement('div');
      notification.className = 'fixed top-4 right-4 z-50 px-4 py-3 rounded-lg shadow-lg flex items-center gap-3 bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400';
      notification.innerHTML = `
        <span class="material-symbols-outlined">check_circle</span>
        <span class="font-medium">${message}</span>
        <button class="close-notification ml-4 text-lg">&times;</button>
      `;
      
      notification.id = 'templateAppliedNotification';
      document.body.appendChild(notification);
      
      // Set up close button
      const closeBtn = notification.querySelector('.close-notification');
      closeBtn.addEventListener('click', () => {
        document.body.removeChild(notification);
      });
      
      // Auto-remove after 3 seconds
      setTimeout(() => {
        if (document.body.contains(notification)) {
          document.body.removeChild(notification);
        }
      }, 3000);
    }
  }
  
  /**
   * Highlight the form section briefly.
   */
  highlightFormSection() {
    const formSection = document.querySelector('section:first-of-type');
    if (!formSection) return;
    
    // Add highlight class
    formSection.classList.add('ring-2', 'ring-primary', 'ring-offset-2', 'rounded-xl');
    
    // Remove highlight after 1.5 seconds
    setTimeout(() => {
      formSection.classList.remove('ring-2', 'ring-primary', 'ring-offset-2', 'rounded-xl');
    }, 1500);
  }
  
  /**
   * Update template-specific UI indicators.
   * @param {Object} template - Applied template
   */
  updateTemplateIndicators(template) {
    // Update any badges or indicators showing current template
    const templateIndicator = document.getElementById('currentTemplateIndicator');
    if (templateIndicator) {
      templateIndicator.textContent = `Using: ${template.name}`;
      templateIndicator.classList.remove('hidden');
    }
    
    // Update template stats if shown
    this.updateTemplateStats(template);
  }
  
  /**
   * Update template statistics display.
   * @param {Object} template - Applied template
   */
  updateTemplateStats(template) {
    // Could show template popularity, success rate, etc.
    const statsContainer = document.getElementById('templateStatsDisplay');
    if (statsContainer) {
      statsContainer.innerHTML = `
        <div class="text-xs text-slate-500 dark:text-slate-400">
          <span class="inline-flex items-center gap-1">
            <span class="material-symbols-outlined text-[12px]">star</span>
            ${template.popularity || 0}% popular
          </span>
          ${template.bpm ? `
            <span class="inline-flex items-center gap-1 ml-3">
              <span class="material-symbols-outlined text-[12px]">speed</span>
              ${template.bpm} BPM
            </span>
          ` : ''}
          ${template.difficulty ? `
            <span class="inline-flex items-center gap-1 ml-3">
              <span class="material-symbols-outlined text-[12px]">bolt</span>
              ${template.difficulty}
            </span>
          ` : ''}
        </div>
      `;
    }
  }
  
  /**
   * Clear currently applied template.
   */
  clearTemplate() {
    // Clear form fields
    if (this.promptInput) this.promptInput.value = '';
    if (this.styleInput) this.styleInput.value = '';
    if (this.titleInput) this.titleInput.value = '';
    
    // Reset character counters
    if (this.promptChars) this.promptChars.textContent = '0/200';
    if (this.styleChars) this.styleChars.textContent = '0/100';
    if (this.titleChars) this.titleChars.textContent = '0/50';
    
    // Reset colors
    [this.promptChars, this.styleChars, this.titleChars].forEach(counter => {
      if (counter) {
        counter.classList.remove('text-red-500', 'text-amber-500');
        counter.classList.add('text-slate-500');
      }
    });
    
    // Hide template indicators
    const templateIndicator = document.getElementById('currentTemplateIndicator');
    if (templateIndicator) templateIndicator.classList.add('hidden');
    
    // Show notification
    this.showNotification('Template cleared. Ready for custom input.');
  }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
  module.exports = TemplateApplier;
} else {
  window.TemplateApplier = TemplateApplier;
}
```

## 5. Integration with Existing App

### File: `app/static/js/app-modular.js` Updates
Add template applier initialization to the main app:

```javascript
// Add to imports/component declarations
let templateApplier;

// Add to createComponents() function
if (window.TemplateApplier) {
  templateApplier = new window.TemplateApplier();
} else {
  console.error('TemplateApplier not available');
}

// Add to initializeComponents() function
// Initialize template applier with form elements
const templateApplierElements = {
  promptInput: DOM.promptInput,
  styleInput: DOM.styleInput,
  instrumentalToggle: DOM.instrumentalToggle,
  modelSelect: DOM.modelSelect,
  promptChars: DOM.promptChars,
  styleChars: DOM.styleChars,
  titleInput: DOM.titleInput,
  titleChars: DOM.titleChars
};

if (templateApplier) {
  templateApplier.initialize(templateApplierElements);
}

// Add to setupEventListeners() function
// Add clear template button if it exists
const clearTemplateBtn = document.getElementById('clearTemplateBtn');
if (clearTemplateBtn && templateApplier) {
  clearTemplateBtn.addEventListener('click', () => {
    templateApplier.clearTemplate();
  });
}
```

### File: `index.html` Updates
Add template indicator and clear button to the form section:

```html
<!-- Add after the prompt textarea (around line 189) -->
<div class="flex items-center justify-between mt-2">
  <div class="flex items-center gap-2">
    <span id="currentTemplateIndicator" class="hidden inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-primary/10 text-primary">
      <span class="material-symbols-outlined text-[14px]">auto_awesome</span>
      <span>Using: Template Name</span>
    </span>
    <button id="clearTemplateBtn" class="hidden text-xs text-slate-500 hover:text-slate-700 dark:hover:text-slate-300 flex items-center gap-1">
      <span class="material-symbols-outlined text-[14px]">close</span>
      Clear
    </button>
  </div>
  <div id="templateStatsDisplay" class="text-xs text-slate-500 dark:text-slate-400">
    <!-- Template stats will be inserted here -->
  </div>
</div>
```

## 6. User Experience Enhancements

### Visual Feedback States
1. **Template Applied State**:
   - Form section gets subtle highlight (ring animation)
   - Success notification appears
   - Template name badge shows above form
   - Generate button becomes active (if audio source selected)

2. **Template Editing State**:
   - Template badge remains visible
   - Clear template button appears
   - Form validation updates in real-time

3. **Template Cleared State**:
   - Template badge disappears
   - Form returns to empty state
   - Notification confirms clearance

### Keyboard Shortcuts
- `Ctrl/Cmd + T` - Open template gallery
- `Escape` - Clear current template
- `Enter` - Apply selected template (when focused in gallery)

### Accessibility Features
- ARIA labels for template application
- Keyboard navigation through template gallery
- Screen reader announcements for template application
- Focus management after template application

## 7. Error Handling

### Common Scenarios
1. **Template Not Found**: Show error message and suggest similar templates
2. **Form Validation Failed**: Highlight invalid fields and provide guidance
3. **Network Error**: Retry mechanism with exponential backoff
4. **Corrupted Template Data**: Fallback to default template structure

### Error Recovery
```javascript
async function applyTemplateWithRetry(templateId, maxRetries = 3) {
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      const response = await fetch(`/api/templates/${templateId}`);
      const data = await response.json();
      
      if (data.success) {
        return templateApplier.applyTemplate(data.template);
      } else {
        throw new Error(data.error || 'Template not found');
      }
    } catch (error) {
      if (attempt === maxRetries) {
        showError(`Failed to apply template: ${error.message}`);
        // Fallback to local template data if available
        applyLocalTemplateFallback(templateId);
      } else {
        // Wait before retry (exponential backoff)
        await new Promise(resolve => setTimeout(resolve, 1000 * attempt));
      }
    }
  }
}
```

## 8. Performance Considerations

### Optimizations
1. **Template Caching**: Cache template data locally to reduce API calls
2. **Lazy Loading**: Load template details only when needed
3. **Debounced Updates**: Debounce form validation updates
4. **Memory Management**: Clean up event listeners and DOM elements

### Bundle Size
- Tree-shake unused template features
- Code-split template gallery component
- Lazy load template images

## 9. Testing Strategy

### Unit Tests
```javascript
describe('TemplateApplier', () => {
  let templateApplier;
  let mockFormElements;
  
  beforeEach(() => {
    templateApplier = new TemplateApplier();
    mockFormElements = {
      promptInput: { value: '' },
      styleInput: { value: '' },
      instrumentalToggle: { checked: false },
      promptChars: { textContent: '' },
      styleChars: { textContent: '' }
    };
  });
  
  test('applies template to form fields', () => {
    const template = {
      name: 'Test Template',
      prompt: '