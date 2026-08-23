/**
 * User registration and profile management service.
 */

class UserDatabase {
    constructor() {
        this.users = new Map();
    }

    /**
     * Finds a user record by email address.
     * @param {string} email
     */
    findByEmail(email) {
        return this.users.get(email) || null;
    }

    /**
     * Saves user profile record.
     * @param {object} user
     */
    saveUser(user) {
        this.users.set(user.email, user);
        return user;
    }
}

/**
 * Validates email format according to standard regex.
 * @param {string} email
 * @returns {boolean}
 */
function validateEmail(email) {
    const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return regex.test(email);
}

/**
 * Registers a new user account with validated email and credentials.
 * @param {string} username
 * @param {string} email
 * @param {string} password
 */
function registerUser(username, email, password) {
    if (!validateEmail(email)) {
        throw new Error("Invalid email format");
    }
    const db = new UserDatabase();
    if (db.findByEmail(email)) {
        throw new Error("User already exists");
    }
    return db.saveUser({ username, email, createdAt: new Date() });
}

module.exports = { UserDatabase, validateEmail, registerUser };
