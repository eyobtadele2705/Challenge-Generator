import {useAuth} from "@clerk/clerk-react";

export const useApi = () => {
    const {getToken} = useAuth();

    const makeRequest = async (endpoint, options = {}) => {
        const token = await getToken();
        const defaultOptions ={
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        }

        const response = await fetch(`http://localhost:8000/api/${endpoint}`,{
            ...defaultOptions,
            ...options
        })
        if (!response.ok) {
            const errorData = await response.json().catch(() => null)
            if (response.status_code === 429) {
                throw new Error("Daily quota limit exceeded. Please try again later.");
            }
            throw new Error(errorData?.detail || 'An Error occurred');
        }
        return response.json();
    }
    return {makeRequest}
}
