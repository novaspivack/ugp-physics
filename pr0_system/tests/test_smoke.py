import numpy as np

def test_import_and_step():
    from pr0_system.forces import strong

    system = strong.BootstrapPR0(L_x=16, L_y=16)
    system.set_soliton(x0=6, y0=8, amplitude=2.5, width=2.0, velocity_x=0.05, charge=+1)
    system.set_soliton(x0=10, y0=8, amplitude=2.5, width=2.0, velocity_x=-0.05, charge=-1)

    for _ in range(10):
        system.step(dt=0.01)

    assert isinstance(system.current_step, int)
    assert np.isfinite(np.max(np.abs(system.psi)**2))


