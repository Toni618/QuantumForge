"""Free real scalar QFT on a 1-D periodic spatial lattice (hbar=c=1).

This is a finite-volume, finite-lattice Gaussian theory, not interacting QFT.
The lattice Laplacian gives omega_k^2=m^2+(2/a sin(pi*k/N))^2.
"""
from __future__ import annotations
import numpy as np

def free_scalar_lattice(mass: float, sites: int = 64, spacing: float = 0.25):
    if not np.isfinite(mass) or mass < 0: raise ValueError("mass must be finite and non-negative")
    if not isinstance(sites, int) or sites < 4 or sites > 4096: raise ValueError("sites must be an integer in [4,4096]")
    if not np.isfinite(spacing) or spacing <= 0: raise ValueError("spacing must be finite and positive")
    k = np.arange(sites)
    p = 2.0 / spacing * np.sin(np.pi*k/sites)
    omega = np.sqrt(mass*mass + p*p)
    vacuum_energy = 0.5*float(np.sum(omega))
    # Equal-time covariance <phi_j phi_0> = (1/N) sum_k exp(2pi i k j/N)/(2 omega_k).
    if np.any(omega == 0):
        covariance = None
        infrared_note = "Massless periodic zero mode makes the field variance infrared divergent; covariance omitted."
    else:
        covariance = np.fft.ifft(1.0/(2.0*omega)).real.tolist()
        infrared_note = None
    return {"theory":"free real scalar field on a 1-D periodic spatial lattice",
            "approximation":"finite lattice and finite periodic volume; Gaussian/free field only",
            "units":"natural units hbar=c=1", "mass":float(mass), "sites":sites,
            "spacing":float(spacing), "length":float(sites*spacing),
            "mode_frequencies":omega.tolist(), "vacuum_energy_lattice":vacuum_energy,
            "equal_time_field_covariance":covariance,
            "infrared_note":infrared_note,
            "dispersion":"omega_k^2 = m^2 + (2/a sin(pi k/N))^2"}
