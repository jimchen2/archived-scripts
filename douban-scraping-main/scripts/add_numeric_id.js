var collections = db.getCollectionNames();
collections.forEach(function(collectionName){
  if(collectionName.startsWith("comments.")){
    print("Processing collection:", collectionName);
    var collection = db.getCollection(collectionName);
    collection.find().forEach(function(doc) {
        var newId = parseInt(doc._id);
        if (!isNaN(newId)) { // check if _id can be converted to a number
            collection.updateOne(
                { _id: doc._id },
                { $set: { numericId: newId } }
            );
        }
    });
  }
});
