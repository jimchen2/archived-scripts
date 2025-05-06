import React from "react";

// Define the component that receives props: projectParticipants and setProjectParticipants
const ProjectParticipantsInput = ({
  projectParticipants,
  setProjectParticipants,
}) => {
  // Handler to add a new participant
  const handleAddParticipant = () => {
    const newKey = `participant_${Date.now()}`; // Unique key based on timestamp
    setProjectParticipants({
      ...projectParticipants,
      [newKey]: { teacherId: "", ranking: 1, funding: 0 },
    }); // Add a new participant with default values
  };

  // Handler to delete a participant by key
  const handleDeleteParticipant = (key) => {
    const newProjectParticipants = { ...projectParticipants }; // Copy the current participants
    delete newProjectParticipants[key]; // Delete the participant with the given key
    setProjectParticipants(newProjectParticipants); // Update the state
  };

  // Handler to update participant's fields
  const handleParticipantChange = (key, field, value) => {
    setProjectParticipants({
      ...projectParticipants,
      [key]: { ...projectParticipants[key], [field]: value }, // Update the specific field of the participant
    });
  };

  return (
    <div className="mb-4">
      <label className="block text-gray-700 font-bold mb-2">
        Participants:
      </label>
      {Object.keys(projectParticipants).map((key) => (
        <div key={key} className="mb-2 flex items-center space-x-2">
          <input
            type="text"
            placeholder="Teacher ID"
            value={projectParticipants[key].teacherId}
            onChange={(e) =>
              handleParticipantChange(key, "teacherId", e.target.value)
            }
            required
            maxLength={5}
            className="w-1/4 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
          />
          <input
            type="number"
            placeholder="Ranking"
            value={projectParticipants[key].ranking}
            onChange={(e) =>
              handleParticipantChange(key, "ranking", parseInt(e.target.value))
            }
            className="w-1/4 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
          />
          <input
            type="number"
            placeholder="Funding"
            value={projectParticipants[key].funding}
            onChange={(e) =>
              handleParticipantChange(
                key,
                "funding",
                parseFloat(e.target.value)
              )
            }
            className="w-1/4 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
          />
          <button
            type="button"
            onClick={() => handleDeleteParticipant(key)}
            className="px-3 py-2 bg-red-500 text-white rounded-md"
          >
            Delete
          </button>
        </div>
      ))}
      <button
        type="button"
        onClick={handleAddParticipant}
        className="px-3 py-2 bg-blue-500 text-white rounded-md mt-2"
      >
        Add Participant
      </button>
    </div>
  );
};

export default ProjectParticipantsInput;
