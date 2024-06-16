import mongoose, { Mongoose } from "mongoose";

const MONGODB_URI: string =
  process.env.MONGODB_URI || "mongodb://localhost:27017/test";

interface MongooseCache {
  conn: Mongoose | null;
  promise: Promise<Mongoose> | null;
}

declare global {
  // Allow the use of `global.mongoose` throughout your project
  var mongoose: MongooseCache | undefined;
}

// Create a cache object if not already present in the global object
let cached: MongooseCache = global.mongoose || { conn: null, promise: null };

if (!global.mongoose) {
  global.mongoose = cached;
}

async function dbConnect(): Promise<Mongoose> {
  if (cached.conn) {
    return cached.conn;
  }

  if (!cached.promise) {
    const opts = {
      bufferCommands: false,
    };

    cached.promise = mongoose.connect(MONGODB_URI, opts).then((mongoose) => {
      return mongoose;
    });
  }

  cached.conn = await cached.promise;
  return cached.conn;
}

export default dbConnect;
