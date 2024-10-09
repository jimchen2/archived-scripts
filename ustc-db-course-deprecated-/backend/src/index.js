const initializeApp = require("./app");
const port = process.env.PORT || 3000;

initializeApp()
  .then((app) => {
    app.listen(port, () => {
      console.log(`Server is running on port ${port}`);
    });
  })
  .catch((error) => {
    console.error("Failed to start the server:", error);
    process.exit(1);
  });