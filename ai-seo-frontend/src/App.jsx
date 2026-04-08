import React, { useState } from "react";
import { CustomerPage } from "./pages/CustomerPage.jsx";
import { AdminPage } from "./pages/AdminPage.jsx";
import { Tabs } from "./components/ui/index.jsx";

const TABS = [
  { id: "customer", label: "Customer Portal", icon: "◈" },
  { id: "admin", label: "Admin Dashboard", icon: "⊞" },
];

export default function App() {
  const [activeTab, setActiveTab] = useState("customer");

  return (
    <div className="app">
      <header className="app-header">
        <div className="app-header-inner">
          <div className="app-logo">
            <span className="logo-mark">⬡</span>
            <span className="logo-text">SEO<em>sync</em></span>
          </div>
          <Tabs tabs={TABS} active={activeTab} onChange={setActiveTab} />
        </div>
      </header>

      <main className="app-main">
        {activeTab === "customer" && <CustomerPage />}
        {activeTab === "admin" && <AdminPage />}
      </main>

      <footer className="app-footer">
        <span>AI SEO System · Powered by FastAPI + Squarespace</span>
      </footer>
    </div>
  );
}
