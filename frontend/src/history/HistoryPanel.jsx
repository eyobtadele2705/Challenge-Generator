import "react"
import {useState, useEffect} from "react";
import {MCQChallenge} from "../challenge/MCQChallenge.jsx";
import {useApi} from "../util/api.js";

export function HistoryPanel() {
    const [history, setHistory] = useState([])
    const [isLoading, setIsLoading] = useState(true)
    const [error, setError] = useState(null)
    const {makeRequest} = useApi()

    useEffect(() => {
        fetchHistory()
    }, []);
    const fetchHistory = async () => {
        setIsLoading(true)
        setError(null)
        try {
            const response = await makeRequest('my-history');
            console.log(response)
            setHistory(response.challenges);
        } catch (err) {
            console.log(err)
            setError(err.message || "Failed to fetch history")
        } finally {
            setIsLoading(false)
        }
    }

    if (isLoading){
        return <div className="loading">
            Loading History...
        </div>
    }
    if (error){
        return <div className="error-message">
            <p>{error}</p>
            <button onClick={fetchHistory}>Retry</button>
        </div>
    }
    return <div className="history-panel">
        <h2>History</h2>
        {history.length===0 ? <p>No history available.</p>
        : <div className="history-list">
            {history.map((challenge) => {
                return <MCQChallenge
                    challenge={challenge}
                    key={challenge.id}
                    showExplanation
                />
            })}
            </div>
        }

    </div>
}