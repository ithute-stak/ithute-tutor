import { AUTH_ENDPOINTS } from "@/api/auth/endpoint";
import api from "@/lib/axios-setup";
import type { LoginResponse } from "@/types/user";

export const login = async (email: string, password: string): Promise<LoginResponse> => {
    const response = await api.post<LoginResponse>(
        AUTH_ENDPOINTS.LOGIN,
        { email, password },
        { withCredentials: true, skipAuthRefresh: true },
    );
    return response.data;
};

export const refreshToken = async () => {
    const response = await api.post(
        AUTH_ENDPOINTS.REFRESH,
        {},
        { withCredentials: true, skipAuthRefresh: true },
    );
    return response.data;
};

export const logout = async () => {
    const response = await api.post(
        AUTH_ENDPOINTS.LOGOUT,
        {},
        { withCredentials: true, skipAuthRefresh: true },
    );
    return response.data;
};

export const getCurrentUser = async () => {
    const response = await api.get(
        AUTH_ENDPOINTS.ME,
        { withCredentials: true },
    );
    return response.data;
};
