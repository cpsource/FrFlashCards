/**
 * lesanimaux.js - Session management and page navigation for lesanimaux
 * Manages user progress through web pages and tracks "easy" pages
 */

// Configuration
const STORAGE_KEY = 'lesanimaux_session';

/**
 * Create or retrieve session data
 * @returns {Object} Session object with easy_web_pages array
 */
function create_session() {
    // Check if session already exists
    let session = localStorage.getItem(STORAGE_KEY);
    
    if (session) {
        // Session exists, parse and return it
        try {
            return JSON.parse(session);
        } catch (e) {
            console.error('Error parsing session data:', e);
            // If corrupted, create new session
        }
    }
    
    // Create new session
    const newSession = {
        easy_web_pages: [],
        created_at: new Date().toISOString(),
        last_updated: new Date().toISOString()
    };
    
    // Save to localStorage
    localStorage.setItem(STORAGE_KEY, JSON.stringify(newSession));
    
    return newSession;
}

/**
 * Get current session
 * @returns {Object} Current session object
 */
function get_session() {
    return create_session(); // This will get existing or create new
}

/**
 * Save session data to localStorage
 * @param {Object} session - Session object to save
 */
function save_session(session) {
    session.last_updated = new Date().toISOString();
    localStorage.setItem(STORAGE_KEY, JSON.stringify(session));
}

/**
 * Mark a page as "easy" and add it to the easy_web_pages list
 * @param {number} page_number - The page number to mark as easy
 * @returns {boolean} True if successfully added, false if already exists
 */
function mark_page_as_easy(page_number) {
    const session = get_session();
    
    // Check if page is already marked as easy
    if (session.easy_web_pages.includes(page_number)) {
        console.log(`Page ${page_number} is already marked as easy`);
        return false;
    }
    
    // Add page to easy list
    session.easy_web_pages.push(page_number);
    
    // Sort the array to keep it organized
    session.easy_web_pages.sort((a, b) => a - b);
    
    // Save updated session
    save_session(session);
    
    console.log(`Page ${page_number} marked as easy`);
    return true;
}

/**
 * Remove a page from the easy list (in case user wants to practice it again)
 * @param {number} page_number - The page number to remove from easy list
 * @returns {boolean} True if successfully removed, false if not in list
 */
function unmark_page_as_easy(page_number) {
    const session = get_session();
    
    const index = session.easy_web_pages.indexOf(page_number);
    
    if (index === -1) {
        console.log(`Page ${page_number} is not in the easy list`);
        return false;
    }
    
    // Remove page from easy list
    session.easy_web_pages.splice(index, 1);
    
    // Save updated session
    save_session(session);
    
    console.log(`Page ${page_number} removed from easy list`);
    return true;
}

/**
 * Check if a page is marked as easy
 * @param {number} page_number - The page number to check
 * @returns {boolean} True if page is easy, false otherwise
 */
function is_page_easy(page_number) {
    const session = get_session();
    return session.easy_web_pages.includes(page_number);
}

/**
 * Get the next non-easy page number
 * @param {number} current_page - Current page number
 * @param {number} max_pages - Maximum number of pages (optional, defaults to 100)
 * @returns {number} Next non-easy page number, or null if all pages are easy
 */
function next_page(current_page, max_pages = 100) {
    const session = get_session();
    
    // Start searching from the next page
    let next = current_page + 1;
    
    // Loop through pages, wrapping around if necessary
    let attempts = 0;
    const max_attempts = max_pages;
    
    while (attempts < max_attempts) {
        // Wrap around to page 1 if we exceed max_pages
        if (next > max_pages) {
            next = 1;
        }
        
        // If this page is not marked as easy, return it
        if (!session.easy_web_pages.includes(next)) {
            return next;
        }
        
        // Try next page
        next++;
        attempts++;
    }
    
    // All pages are marked as easy
    console.log('All pages are marked as easy!');
    return null;
}

/**
 * Get statistics about progress
 * @param {number} max_pages - Maximum number of pages (defaults to 100)
 * @returns {Object} Statistics object
 */
function get_statistics(max_pages = 100) {
    const session = get_session();
    
    return {
        total_pages: max_pages,
        easy_pages: session.easy_web_pages.length,
        remaining_pages: max_pages - session.easy_web_pages.length,
        percentage_complete: Math.round((session.easy_web_pages.length / max_pages) * 100),
        easy_page_list: session.easy_web_pages
    };
}

/**
 * Reset the session (clear all progress)
 */
function reset_session() {
    localStorage.removeItem(STORAGE_KEY);
    console.log('Session reset');
    return create_session();
}

/**
 * Export session data as JSON string (for backup)
 * @returns {string} JSON string of session data
 */
function export_session() {
    const session = get_session();
    return JSON.stringify(session, null, 2);
}

/**
 * Import session data from JSON string (for restore)
 * @param {string} jsonString - JSON string of session data
 * @returns {boolean} True if successful, false otherwise
 */
function import_session(jsonString) {
    try {
        const session = JSON.parse(jsonString);
        
        // Validate session structure
        if (!session.easy_web_pages || !Array.isArray(session.easy_web_pages)) {
            console.error('Invalid session data structure');
            return false;
        }
        
        localStorage.setItem(STORAGE_KEY, jsonString);
        console.log('Session imported successfully');
        return true;
    } catch (e) {
        console.error('Error importing session:', e);
        return false;
    }
}

// Initialize session on load
create_session();

// Log session info to console for debugging
console.log('lesanimaux.js loaded');
console.log('Current session:', get_session());
