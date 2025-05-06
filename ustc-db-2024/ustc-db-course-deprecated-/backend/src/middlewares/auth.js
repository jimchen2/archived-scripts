const { expressjwt: jwt } = require('express-jwt');

const secret = process.env.JWT_SECRET;

if (!secret) {
    throw new Error('JWT_SECRET environment variable is not set');
}

const auth = jwt({
    secret: secret,
    algorithms: ['HS256'],
    getToken: req => {
        if (req.headers.authorization && req.headers.authorization.split(' ')[0] === 'Bearer') {
            return req.headers.authorization.split(' ')[1];
        }
        return null;
    }
});

// Add this logging middleware
function logAuthInfo(req, res, next) {
    console.log('Token:', req.headers.authorization);
    console.log('Decoded token:', req.auth);
    next();
}

// Error handling for JWT authentication
function handleAuthErrors(err, req, res, next) {
    if (err.name === 'UnauthorizedError') {
        res.status(401).send('Invalid token');
    } else {
        next(err);
    }
}

// Middleware to check for superadmin
function checkSuperadmin(req, res, next) {
    if (req.auth.id !== '-1') {
        return res.status(403).send('Access denied');
    }
    next();
}

module.exports = { auth, checkSuperadmin, handleAuthErrors, logAuthInfo };