// This is for VK groups
// Example:
// https://vk.com/tsiskaridzenikolayofficial

// Refer to:
// https://dev.vk.com/en/method/groups.get

// API url example:
// https://api.vk.com/method/groups.getById?group_ids=tsiskaridzenikolayofficial&fields=description,city,photo_100&access_token=ACCESS_TOKEN&v=5.131
// You can change the fields for other information

// API example response:
// {
//     "response": [
//       {
//         "id": 211218365,
//         "city": {
//           "id": 1,
//           "title": "Москва"
//         },
//         "description": "Официальная страница\nНиколая Цискаридзе\n\nРегистрация в перечне РКН: https://gosuslugi.ru/snet/67927d41ee896061c9ca7145\n\nИСКУССТВО и ЖИЗНЬ\n\nПоказывать можно только зрячим. \nПеть песню — только тем, кто слышит. \nДари себя тому, кто будет благодарен, \nКто понимает, любит и ценит\nОмар Хайям\n\nПо всем вопросам tsiskaridzenikolay@gmail.com",
//         "name": "Николай Цискаридзе",
//         "screen_name": "tsiskaridzenikolayofficial",
//         "is_closed": 0,
//         "type": "page",
//         "photo_100": "https://sun6-21.userapi.com/s/v1/ig2/zVU_pWUPn9lmt6mIC51Xi5hfTt7ZpDFY1Ud__KWMrwqU0HwooFB81RkHKj0l4DsVhvHXgj3BQmd7LqqFF1JOR4jB.jpg?quality=95&crop=10,151,643,643&as=32x32,48x48,72x72,108x108,160x160,240x240,360x360,480x480,540x540,640x640&ava=1&cs=100x100"
//       }
//     ]
//   }

// Function params:
// API_KEY

// Function return:
// name, image url, description
// put city into description

export async function getVKGroupInfo(groupId, API_KEY) {
  try {
    // Build the API URL
    const apiUrl = `https://api.vk.com/method/groups.getById?group_ids=${groupId}&fields=description,city,photo_100&access_token=${API_KEY}&v=5.131`;

    // Fetch data from the API
    const response = await fetch(apiUrl);
    const data = await response.json();

    // Check if we received valid data
    if (!data.response || !data.response[0]) {
      throw new Error("Invalid response from VK API");
    }

    const group = data.response[0];

    // Extract the required information
    const result = {
      name: group.name,
      imageUrl: group.photo_100,
      description: group.description || "",
    };

    // Add city to description if available
    if (group.city && group.city.title) {
      result.description = `City: ${group.city.title}\n\n${result.description}`;
    }

    return result;
  } catch (error) {
    console.error("Error fetching VK group info:", error);
    throw error;
  }
}
