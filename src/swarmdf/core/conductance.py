import pandas as pd 
import lompe

# TODO fix documentation 
# TODO add new auroral conductance estimation method!! 

def compute_conductances(conductance_method, start_time, end_time, DT, grids, conductance_params):
    """
    Docstring for compute_conductances
    
    :param conductance_method: Description
    :param start_time: Description
    :param end_time: Description
    :param frame_length: Description
    :param grids: Description
    :param conductance_params: kp, f107 and background values (user-defined)
    """
    print('Conductance method:', conductance_method)

    kp_value, f107_value, background_value = conductance_params['kp'], conductance_params['f107'], conductance_params['background']

    # Define time step edges of analysis interval
    times = pd.date_range(start=start_time, end=end_time, freq=f'{DT}S', tz=None)

    # Compute central times for each time step (each grid)
    center_times = times[:-1] + pd.to_timedelta(DT/2, unit='s')

    SHs, SPs = [], [] 

    for grid, ct in zip(grids, center_times):

        # time = tm.replace(tzinfo=None) if tm.tzinfo else tm

        # functions for conductances to be passed to the Lompe model
        if conductance_method== 'Hardy model':
            SH = lambda lon = grid.lon, lat = grid.lat: lompe.conductance.hardy_EUV(lon, lat, kp_value, ct, 'hall', F107=f107_value, starlight= background_value) 
            SP = lambda lon = grid.lon, lat = grid.lat: lompe.conductance.hardy_EUV(lon, lat, kp_value, ct, 'pedersen', F107=f107_value, starlight = background_value)
            SHs.append(SH)
            SPs.append(SP)
        if conductance_method== 'Zang & Paxton model':
            SH = lambda lon = grid.lon, lat = grid.lat: lompe.conductance.ZhangPaxton_EUV(lon, lat, kp_value, ct, 'hall', F107=f107_value, starlight= background_value) 
            SP = lambda lon = grid.lon, lat = grid.lat: lompe.conductance.ZhangPaxton_EUV(lon, lat, kp_value, ct, 'pedersen', F107=f107_value, starlight = background_value)
            SHs.append(SH)
            SPs.append(SP)
        else:
            raise ValueError(
                f"Unknown conductance method: {conductance_method}. "
                "Must be one of ['Hardy model', 'Zhang & Paxton model']")
        
    return SHs, SPs