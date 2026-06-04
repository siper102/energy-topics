import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { setupService } from '../services/api';

interface Setup {
  id: number;
  name: string;
  max_capacity_kwh: number;
  max_power_kw: number;
  efficiency_charge: number;
  efficiency_discharge: number;
  initial_soc_kwh: number;
  lat: number;
  lon: number;
  peak_power_kw: number;
  tilt: number;
  azimuth: number;
}

interface SetupContextType {
  setups: Setup[];
  activeSetup: Setup | null;
  setActiveSetupId: (id: number) => void;
  loading: boolean;
  refreshSetups: () => Promise<void>;
}

const SetupContext = createContext<SetupContextType | undefined>(undefined);

export const SetupProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [setups, setSetups] = useState<Setup[]>([]);
  const [activeSetup, setActiveSetup] = useState<Setup | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchSetups = async () => {
    setLoading(true);
    try {
      const data = await setupService.listSetups();
      setSetups(data);
      if (data.length > 0 && !activeSetup) {
        // Default to first setup or one from local storage
        const savedId = localStorage.getItem('activeSetupId');
        const initial = savedId ? data.find((s: Setup) => s.id === parseInt(savedId)) || data[0] : data[0];
        setActiveSetup(initial);
      }
    } catch (error) {
      console.error("Failed to fetch setups", error);
    }
    setLoading(false);
  };

  useEffect(() => {
    fetchSetups();
  }, []);

  const setActiveSetupId = (id: number) => {
    const setup = setups.find(s => s.id === id);
    if (setup) {
      setActiveSetup(setup);
      localStorage.setItem('activeSetupId', id.toString());
    }
  };

  return (
    <SetupContext.Provider value={{ setups, activeSetup, setActiveSetupId, loading, refreshSetups: fetchSetups }}>
      {children}
    </SetupContext.Provider>
  );
};

export const useSetups = () => {
  const context = useContext(SetupContext);
  if (context === undefined) {
    throw new Error('useSetups must be used within a SetupProvider');
  }
  return context;
};
