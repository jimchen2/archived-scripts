```js
// Script to extract cookies
const cookies = document.cookie
  .split('; ')
  .map(cookie => {
    const [name, value] = cookie.split('=');
    return { name, value, domain: '.tandem.net', path: '/' };
  });

// Format as JSON and copy to clipboard
const cookiesJSON = JSON.stringify(cookies, null, 2);
console.log(cookiesJSON);
copy(cookiesJSON); // This will copy to clipboard in most modern browsers
console.log('Cookies copied to clipboard. Paste into cookies.json file.');
```