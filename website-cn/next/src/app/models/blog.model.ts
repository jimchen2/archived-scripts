import mongoose, { Schema, Document, Model } from "mongoose";

interface IBlog extends Document {
  title: string;
  date: string;
  type: string;
  body: string;
}

const blogSchema: Schema = new Schema(
  {
    title: {
      type: String,
      default: "",
    },
    date: {
      type: String,
      default: "",
    },
    type: {
      type: String,
      default: "",
    },
    body: {
      type: String,
      default: "",
    },
  },
  { versionKey: false, collection: "translated_blog" }  
);

const Blog: Model<IBlog> =
  mongoose.models.Blog || mongoose.model<IBlog>("Blog", blogSchema);

export default Blog;
