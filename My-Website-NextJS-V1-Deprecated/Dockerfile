# Use the official Node.js image as a base
FROM node:20-alpine

# Create and change to the app directory
WORKDIR /app

# Install Git and other dependencies
RUN apk add --no-cache git

# Clone the repository
# Replace 'https://github.com/jimchen2/nextjs-tube' with the actual repository URL
RUN git clone https://github.com/jimchen2/My-Website-New .

# Install dependencies
RUN npm install

# Install NextJS
RUN npm install next

# Build the Next.js app
RUN npm run build

# Expose the port the app runs on
EXPOSE 3000

# Run the Next.js app
CMD ["npm", "start"]