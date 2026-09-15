"use client";

import React, { useState } from "react";
import { useSearchParams } from "next/navigation";
import { Loader2, ShieldCheck } from "lucide-react";
import { toast } from "sonner";

import { login } from "@/api/auth/actions";
import { Button } from "@/components/ui/button";
import {
    Card,
    CardContent,
    CardDescription,
    CardHeader,
    CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { PasswordInput } from "@/components/customUI/password-input";


export const LoginCard = () => {
    const searchParams = useSearchParams();
    const [loading, setLoading] = useState(false);
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");

    const handleLogin = async (event: React.FormEvent<HTMLFormElement>) => {
        event.preventDefault();
        setLoading(true);
        try {
            await login(email, password);
            toast.success("Welcome back to Tutor");

            const requested = searchParams.get("next");
            const destination = requested?.startsWith("/") && !requested.startsWith("//")
                ? requested
                : "/dashboard";
            // The backend has set Tutor-owned HttpOnly session cookies. A full
            // navigation lets AuthProvider bootstrap from that authoritative session.
            window.location.replace(destination);
        } catch (error) {
            const message =
                error && typeof error === "object" && "response" in error
                    ? "Invalid email or password"
                    : error instanceof Error
                        ? error.message
                        : "Unable to sign in to Tutor";
            toast.error(message);
            setLoading(false);
        }
    };

    return (
        <Card className="w-full max-w-md border-0 bg-white/90 shadow-2xl backdrop-blur-xl rounded-2xl">
            <CardHeader className="space-y-2 text-center">
                <div className="mx-auto flex size-12 items-center justify-center rounded-full bg-slate-950 text-white">
                    <ShieldCheck className="size-6" />
                </div>
                <CardTitle className="text-2xl font-semibold">Sign in to Ithute Tutor</CardTitle>
                <CardDescription>
                    Use your Tutor account. Tutor authentication is managed independently by this system.
                </CardDescription>
            </CardHeader>

            <CardContent>
                <form onSubmit={handleLogin} className="grid gap-4">
                    <div className="grid gap-2">
                        <Label htmlFor="email">Email</Label>
                        <Input
                            id="email"
                            type="email"
                            autoComplete="email"
                            value={email}
                            onChange={(event) => setEmail(event.target.value)}
                            required
                            disabled={loading}
                        />
                    </div>
                    <div className="grid gap-2">
                        <Label htmlFor="password">Password</Label>
                        <PasswordInput
                            id="password"
                            autoComplete="current-password"
                            value={password}
                            onChange={(event) => setPassword(event.target.value)}
                            required
                            disabled={loading}
                        />
                    </div>
                    <Button className="h-11 w-full text-base font-medium" type="submit" disabled={loading}>
                        {loading && <Loader2 className="mr-2 size-5 animate-spin" />}
                        Sign in
                    </Button>
                </form>
            </CardContent>
        </Card>
    );
};
