// This can be used for both accounts and groups
// Example:
// https://vk.com/tutberidze.eteri

// Refer to:
// https://dev.vk.com/en/method/wall.get

// API url example:
// https://api.vk.com/method/wall.get?owner_id=tutberidze.eteri&count=20&access_token=ACCESS_TOKEN&v=5.131
// https://api.vk.com/method/wall.get?owner_id=tsiskaridzenikolayofficial&count=20&access_token=ACCESS_TOKEN&v=5.131

// API example response:

// {
//     "response": {
//       "count": 74,
//       "items": [
//         {
//           "inner_type": "wall_wallpost",
//   ...
// }
// }

// Each Item:
// {
// ...
//     "attachments": [
// ...
//     ],
//     "date": 1741546333,
//     "edited": 1741546346,
//  ...
//     "text": "Приглашаю вас на ледовое шоу #TeamTutberidze! \n\nВас ждут новые истории и легендарные программы в исполнении одних из лучших фигуристов в мире.\n\nЖду встречи с каждым из вас в 11 городах!\n\nСсылка на билеты в шапке профиля.",
//     "views": {
//       "count": 1601
//     }
//   },

// Photo Attachments:
//       {
//         "type": "photo",
//         "photo": {
//          ...
//           "sizes": [
//             {
//               "height": 75,
//               "type": "s",
//               "width": 75,
//               "url": "https://sun6-21.userapi.com/s/v1/ig2/GYs-E55vvY2132z9DgSoTvPO0Sk0Iely8Tp5RSZZB_wEMwfsZCWaM_pJUHuZm4W0l_NaaRQGT-e5m1Y3dOfrxqMx.jpg?quality=95&as=32x32,48x48,72x72,108x108,160x160,240x240,360x360,480x480,540x540,640x640,720x720,1080x1080&from=bu&cs=75x75"
//             },
//          ...
//           ],
//           "orig_photo": {
//             "height": 1080,
//             "type": "base",
//             "url": "https://sun6-21.userapi.com/s/v1/ig2/GYs-E55vvY2132z9DgSoTvPO0Sk0Iely8Tp5RSZZB_wEMwfsZCWaM_pJUHuZm4W0l_NaaRQGT-e5m1Y3dOfrxqMx.jpg?quality=95&as=32x32,48x48,72x72,108x108,160x160,240x240,360x360,480x480,540x540,640x640,720x720,1080x1080&from=bu",
//             "width": 1080
//           }
//         }
//       }

// Video Attachments:
// Construct the url: https://vk.com/video643779055_456241376
// Embed Example:
// <iframe src="https://vk.com/video_ext.php?oid=643779055&id=456241376&hd=2&autoplay=1"
// width="853" height="480" allow="autoplay; encrypted-media; fullscreen; picture-in-picture;
// screen-wake-lock;" frameborder="0" allowfullscreen></iframe>

// "attachments": [
//     {
//       "type": "video",
//       "video": {
// ...
//         "image": [
//           {
// ...
//         ],
//         "first_frame": [
//           {
// ...
//         ],
//         "width": 720,
//         "height": 1280,
//         "id": 456241376,
//         "owner_id": 643779055,
//         "title": "Видео от Этери Тутберидзе",
// ...

// Function params:
// username, API_KEY

// Function return:
// title, link, date, article html(text, images, videos)

export async function getVKPosts(username, apiKey, count = 15) {
  try {
    // Build the API URL
    const apiUrl = `https://api.vk.com/method/wall.get?domain=${username}&count=${count}&access_token=${apiKey}&v=5.131`;

    // Fetch data from VK API
    const response = await fetch(apiUrl);
    const data = await response.json();

    if (!data.response || !data.response.items || data.response.items.length === 0) {
      throw new Error("No posts found or invalid response");
    }

    // Process each post
    const posts = data.response.items.map((post) => {
      // Convert Unix timestamp to readable date
      const postDate = new Date(post.date * 1000);
      const formattedDate = postDate.toLocaleString();

      // Create post link
      const postLink = `https://vk.com/${username}?w=wall${post.owner_id}_${post.id}`;

      // Process text content
      let postText = post.text || "";
      // Convert line breaks to HTML
      postText = postText.replace(/\n/g, "<br>");
      // Convert hashtags to links
      postText = postText.replace(/#(\w+)/g, '<a href="https://vk.com/feed?section=search&q=%23$1">#$1</a>');

      // Process attachments
      let attachmentsHtml = "";

      if (post.attachments && post.attachments.length > 0) {
        // Process photos
        const photos = post.attachments.filter((att) => att.type === "photo");
        if (photos.length > 0) {
          attachmentsHtml += '<div class="post-photos">';
          photos.forEach((photoAtt) => {
            // Use orig_photo if available, otherwise find the largest size
            let photoUrl, photoWidth, photoHeight;

            if (photoAtt.photo.orig_photo) {
              photoUrl = photoAtt.photo.orig_photo.url;
              photoWidth = photoAtt.photo.orig_photo.width;
              photoHeight = photoAtt.photo.orig_photo.height;
            } else if (photoAtt.photo.sizes && photoAtt.photo.sizes.length > 0) {
              const largePhoto = photoAtt.photo.sizes.reduce((prev, curr) => (curr.width > prev.width ? curr : prev), photoAtt.photo.sizes[0]);
              photoUrl = largePhoto.url;
              photoWidth = largePhoto.width;
              photoHeight = largePhoto.height;
            }

            attachmentsHtml += `<div class="post-photo">
                <img src="${photoUrl}" alt="Post image" width="${photoWidth}" height="${photoHeight}" />
              </div>`;
          });
          attachmentsHtml += "</div>";
        }

        // Process videos
        const videos = post.attachments.filter((att) => att.type === "video");
        if (videos.length > 0) {
          attachmentsHtml += '<div class="post-videos">';
          videos.forEach((videoAtt) => {
            const video = videoAtt.video;
            const videoUrl = `https://vk.com/video${video.owner_id}_${video.id}`;
            const embedUrl = `https://vk.com/video_ext.php?oid=${video.owner_id}&id=${video.id}&hd=2`;

            // Use thumbnail as preview if available
            let thumbnailUrl = "";
            if (video.image && video.image.length > 0) {
              // Get the largest available thumbnail
              const largestImage = video.image.reduce((prev, curr) => (curr.width > prev.width ? curr : prev), video.image[0]);
              thumbnailUrl = largestImage.url;
            }

            attachmentsHtml += `<div class="post-video">
                <iframe src="${embedUrl}" 
                  width="640" height="360" 
                  allow="autoplay; encrypted-media; fullscreen; picture-in-picture; screen-wake-lock;" 
                  frameborder="0" allowfullscreen>
                </iframe>
                <a href="${videoUrl}" target="_blank">Watch on VK</a>
              </div>`;
          });
          attachmentsHtml += "</div>";
        }
      }

      // Combine text and attachments into full HTML article
      const articleHtml = `
          <div class="vk-post">
            <div class="post-text">${postText}</div>
            ${attachmentsHtml}
          </div>
        `;

      // Create post title from first 50 chars of text or default
      const title = post.text ? (post.text.length > 50 ? post.text.substring(0, 50) + "..." : post.text) : `Post by ${username}`;

      return {
        title,
        link: postLink,
        date: formattedDate,
        articleHtml,
      };
    });

    return posts;
  } catch (error) {
    console.error("Error fetching VK posts:", error);
    throw error;
  }
}
