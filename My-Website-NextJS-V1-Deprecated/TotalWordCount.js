use test

var pipeline = [
  {
    $project: {
      body: 1
    }
  }
];

function countWords(str) {
  return str.trim().split(/\s+/).length;
}

var totalWords = 0;

db.documents.aggregate(pipeline).forEach(function(doc) {
  if (doc.body) {
    totalWords += countWords(doc.body);
  }
});

print(totalWords);
