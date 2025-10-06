import "react"
import {useState} from "react";

export function MCQChallenge(challenge, showExplanation = false) {
    const [selectedOption, setSelectedOption] = useState(null);
    const [shouldShowExplanation, setShouldShowExplanation] = useState(showExplanation);


    challenge = challenge.challenge

    const options = typeof challenge.challenge === 'string'
        ? JSON.parse(challenge.options)
        : challenge.options;


    const handleOptionSelect = (index) => {

        console.log("option selected " + index)
        if (selectedOption !== null) return;
        setSelectedOption(index);
        if (selectedOption === challenge.correct_answer_id) {
            console.log("correct answer selected")
        }
        setShouldShowExplanation(true);

    }
    const getOptionClass = (index) => {
        if (selectedOption === null) return 'option';
        console.log("selected option " + selectedOption + " correct answer " + challenge.correct_answer_id)
        if ((index).toString() === challenge.correct_answer_id) {
            return 'option correct';
        }
        if (selectedOption === index && index !== challenge.correct_answer_id) {
            return 'option incorrect';
        }
        return 'option';
    }
    return <div className="challenge-display">
        <p><strong>Difficulty</strong>: {challenge.difficulty}</p>
        <p className="challenge-title"> {challenge.title}</p>
        <div className="options">
            {options.map((option, index) => (
                <div
                    className={getOptionClass(index)}
                    key={index}
                    onClick={() => handleOptionSelect(index)}
                >
                    {option}
                </div>
            ))}
        </div>
        {shouldShowExplanation && selectedOption !== null && (
            <div className="explanation">
                <h4>Explanation</h4>
                <p>{challenge.explanation}</p>
            </div>
        )}
    </div>
}