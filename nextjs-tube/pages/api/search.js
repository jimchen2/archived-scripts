import dbConnect from "../../lib/mongoose";
import Video from "../../models/Video";

export default async (req, res) => {
  await dbConnect();

  if (req.method === "GET") {
    const {
      sort = "random",
      start = 0,
      end = 10,
      language,
      tag,
      query = "",
      filter = "",
    } = req.query;

    try {
      // Build the search query
      let searchQuery = {};

      if (query) {
        searchQuery.filename = { $regex: query, $options: "i" };
      }

      if (language) {
        searchQuery.language = language;
      }

      if (tag) {
        searchQuery.tags = tag;
      }

      // Filter out unwanted tags
      if (filter) {
        const filterTags = filter.split(",");
        searchQuery.tags = { $nin: filterTags };
      }

      // Determine the sort order
      let sortOption = {};
      switch (sort) {
        case "createdAt":
          sortOption = { createdAt: -1 };
          break;
        case "filename":
          sortOption = { filename: 1 };
          break;
        case "random":
          sortOption = { $sample: { size: parseInt(end) - parseInt(start) } };
          break;
        // Add more sort options as needed
        default:
          sortOption = { createdAt: -1 };
      }

      // Perform the search
      let videos;
      if (sort === "random") {
        videos = await Video.aggregate([
          { $match: searchQuery },
          { $sample: { size: parseInt(end) - parseInt(start) } },
        ]);
      } else {
        videos = await Video.find(searchQuery)
          .sort(sortOption)
          .skip(parseInt(start))
          .limit(parseInt(end) - parseInt(start));
      } // Count total results for pagination
      const totalCount = await Video.countDocuments(searchQuery);

      // Project only necessary fields
      const projectedVideos = videos.map((video) => ({
        _id: video._id,
        filename: video.filename,
        thumbnailUrl: video.thumbnailUrl,
        previewImageUrl: video.previewImageUrl,
        language: video.language,
        tags: video.tags,
        isMerged: video.isMerged,
      }));

      res.status(200).json({
        videos: projectedVideos,
        totalCount,
      });
    } catch (error) {
      console.error(error);
      res.status(500).json({ error: "Error searching videos" });
    }
  } else {
    res.status(405).json({ error: "Method not allowed" });
  }
};
