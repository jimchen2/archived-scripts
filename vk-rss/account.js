// This is only for personal accounts
// Example:
// https://vk.com/tutberidze.eteri

// Refer to:
// https://dev.vk.com/en/method/users.get

// API url example:
// https://api.vk.com/method/users.get?user_ids=tutberidze.eteri&fields=photo_100,bdate,city,status&access_token=SECRET_KEY&v=5.131
// You can change the fields for other information

// API example response:

// {
//   "response": [
//     {
//       "id": 643779055,
//       "bdate": "24.2.1974",
//       "city": {
//         "id": 1,
//         "title": "Москва"
//       },
//       "status": "Coaching for life 🎗Заслуженный тренер России по фигурному катанию на коньках 🎫Мастер Спорта СССР",
//       "photo_100": "https://sun6-22.userapi.com/s/v1/ig2/VCdpct-dzr6BQTAX1aSh23jqvHDdtx_jCeTBhcRXYW1jM710Mw9HAyfWb1x4f9-7ljAov1BWfhT3D5jqhH38VjDF.jpg?quality=95&crop=1,1,800,800&as=32x32,48x48,72x72,108x108,160x160,240x240,360x360,480x480,540x540,640x640,720x720&ava=1&cs=100x100",
//       "first_name": "Этери",
//       "last_name": "Тутберидзе",
//       "can_access_closed": true,
//       "is_closed": false
//     }
//   ]
// }

// Function params:
// username, API_KEY

// Function return:
// name, image url, description

export async function getVKProfile(username, API_KEY) {
  try {
    const apiUrl = `https://api.vk.com/method/users.get?user_ids=${username}&fields=photo_100,status,bdate,city&access_token=${API_KEY}&v=5.131`;
    const response = await fetch(apiUrl);
    const data = await response.json();
    if (data.error) {
      throw new Error(`VK API Error: ${data.error.error_msg}`);
    }
    if (!data.response || data.response.length === 0) {
      throw new Error("No user data found");
    }

    const user = data.response[0];

    let description = user.status || "";

    // Add birthdate if available
    if (user.bdate) {
      description += (description ? "\n" : "") + `Born: ${user.bdate}`;
    }

    // Add city if available
    if (user.city && user.city.title) {
      description += (description ? "\n" : "") + `Location: ${user.city.title}`;
    }

    if (!description) {
      description = "";
    }

    return {
      name: `${user.first_name} ${user.last_name}`,
      imageUrl: user.photo_100,
      description: description,
    };
  } catch (error) {
    console.error("Error fetching VK profile:", error);
    throw error;
  }
}
