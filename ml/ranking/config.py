"""
Configuration for vessel ranking module.
"""

import os

class RankingConfig:
    """Configuration for vessel ranking algorithm."""
    
    def __init__(self):
        # Proximity thresholds (in km)
        self.proximity_close = float(os.getenv('RANKING_PROXIMITY_CLOSE', '5'))
        self.proximity_medium = float(os.getenv('RANKING_PROXIMITY_MEDIUM', '15'))
        self.proximity_far = float(os.getenv('RANKING_PROXIMITY_FAR', '35'))
        
        # Timing thresholds (in hours)
        self.timing_immediate = float(os.getenv('RANKING_TIMING_IMMEDIATE', '1'))
        self.timing_recent = float(os.getenv('RANKING_TIMING_RECENT', '3'))
        self.timing_delayed = float(os.getenv('RANKING_TIMING_DELAYED', '8'))
        
        # Trajectory thresholds (in degrees)
        self.trajectory_strong = float(os.getenv('RANKING_TRAJECTORY_STRONG', '35'))
        self.trajectory_moderate = float(os.getenv('RANKING_TRAJECTORY_MODERATE', '80'))
        
        # Prior probabilities
        self.prior_tanker = float(os.getenv('RANKING_PRIOR_TANKER', '0.08'))
        self.prior_other = float(os.getenv('RANKING_PRIOR_OTHER', '0.03'))
        
        # Likelihood ratios
        self.likelihood_proximity_close = float(os.getenv('RANKING_LIKELIHOOD_PROXIMITY_CLOSE', '8.0'))
        self.likelihood_proximity_medium = float(os.getenv('RANKING_LIKELIHOOD_PROXIMITY_MEDIUM', '4.0'))
        self.likelihood_proximity_far = float(os.getenv('RANKING_LIKELIHOOD_PROXIMITY_FAR', '1.6'))
        self.likelihood_proximity_distant = float(os.getenv('RANKING_LIKELIHOOD_PROXIMITY_DISTANT', '0.55'))
        
        self.likelihood_timing_immediate = float(os.getenv('RANKING_LIKELIHOOD_TIMING_IMMEDIATE', '6.0'))
        self.likelihood_timing_recent = float(os.getenv('RANKING_LIKELIHOOD_TIMING_RECENT', '3.0'))
        self.likelihood_timing_delayed = float(os.getenv('RANKING_LIKELIHOOD_TIMING_DELAYED', '1.2'))
        self.likelihood_timing_late = float(os.getenv('RANKING_LIKELIHOOD_TIMING_LATE', '0.45'))
        
        self.likelihood_vessel_type_tanker = float(os.getenv('RANKING_LIKELIHOOD_VESSEL_TYPE_TANKER', '2.5'))
        self.likelihood_vessel_type_other = float(os.getenv('RANKING_LIKELIHOOD_VESSEL_TYPE_OTHER', '0.75'))
        
        self.likelihood_trajectory_strong = float(os.getenv('RANKING_LIKELIHOOD_TRAJECTORY_STRONG', '3.0'))
        self.likelihood_trajectory_moderate = float(os.getenv('RANKING_LIKELIHOOD_TRAJECTORY_MODERATE', '1.6'))
        self.likelihood_trajectory_weak = float(os.getenv('RANKING_LIKELIHOOD_TRAJECTORY_WEAK', '0.7'))
        
        # Behavioral anomaly
        self.behavioral_anomaly_max_gap = float(os.getenv('RANKING_BEHAVIORAL_ANOMALY_MAX_GAP', '60'))
        self.behavioral_anomaly_heading_weight = float(os.getenv('RANKING_BEHAVIORAL_ANOMALY_HEADING_WEIGHT', '0.5'))
        self.behavioral_anomaly_speed_weight = float(os.getenv('RANKING_BEHAVIORAL_ANOMALY_SPEED_WEIGHT', '5'))

    @classmethod
    def get_instance(cls):
        """Return the process configuration, initialized from the environment."""
        if not hasattr(cls, '_instance'):
            cls._instance = cls()
        return cls._instance