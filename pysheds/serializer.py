import json
import numpy as np
from pathlib import Path
from typing import Union, Dict, Any
from pysheds.sgrid import sGrid
from pysheds.sview import Raster, MultiRaster, ViewFinder
from affine import Affine
from pysheds import projection


class PyshedsSerializer:
    """
    Fast JSON + NumPy serialization for pysheds objects.
    Supports sGrid, Raster, and MultiRaster objects.
    """
    
    @staticmethod
    def save_sgrid(grid: sGrid, base_filename: Union[str, Path]) -> None:
        """
        Save an sGrid object using JSON + NumPy format.
        
        Parameters
        ----------
        grid : sGrid
            The sGrid object to save
        base_filename : str or Path
            Base filename (without extension)
        """
        base_path = Path(base_filename)
        base_path.mkdir(parents=True, exist_ok=True)
        
        vf = grid.viewfinder
        
        # Save metadata as JSON
        metadata = {
            'type': 'sGrid',
            'affine': list(vf.affine),
            'shape': vf.shape,
            'nodata': float(vf.nodata) if not np.isnan(vf.nodata) else 'nan',
            'crs': str(vf.crs),
            'mask_shape': vf.mask.shape,
            'mask_dtype': str(vf.mask.dtype)
        }
        
        with open(f"{base_path}_grid.json", 'w') as f:
            json.dump(metadata, f, indent=2)
        
        # Save mask as compressed numpy array
        np.savez_compressed(f"{base_path}_mask.npz", mask=vf.mask)
        
        print(f"sGrid saved to {base_path}.json and {base_path}_mask.npz")

    @staticmethod
    def load_sgrid(base_filename: Union[str, Path]) -> sGrid:
        """
        Load an sGrid object from JSON + NumPy format.
        
        Parameters
        ----------
        base_filename : str or Path
            Base filename (without extension)
            
        Returns
        -------
        sGrid
            The loaded sGrid object
        """
        base_path = Path(base_filename)
        
        # Load metadata
        with open(f"{base_path}_grid.json", 'r') as f:
            metadata = json.load(f)
        
        if metadata['type'] != 'sGrid':
            raise ValueError(f"Expected sGrid, got {metadata['type']}")
        
        # Load mask
        mask_data = np.load(f"{base_path}_mask.npz")
        mask = mask_data['mask']
        
        # Handle NaN nodata values and ensure proper numpy type
        nodata = metadata['nodata']
        if nodata == 'nan':
            nodata = np.nan
        else:
            nodata = np.float64(nodata)
        
        # Reconstruct ViewFinder
        affine = Affine(*metadata['affine'])
        viewfinder = ViewFinder(
            affine=affine,
            shape=tuple(metadata['shape']),
            nodata=nodata,
            mask=mask,
            crs=projection.to_proj(metadata['crs'])
        )
        
        return sGrid(viewfinder)

    @staticmethod
    def save_raster(raster: Union[Raster, MultiRaster], base_filename: Union[str, Path]) -> None:
        """
        Save a Raster or MultiRaster object using JSON + NumPy format.
        
        Parameters
        ----------
        raster : Raster or MultiRaster
            The raster object to save
        base_filename : str or Path
            Base filename (without extension)
        """

        base_path = Path(base_filename)
        base_path.mkdir(parents=True, exist_ok=True)

        vf = raster.viewfinder
        
        # Determine raster type
        raster_type = 'MultiRaster' if isinstance(raster, MultiRaster) else 'Raster'
        
        # Save metadata as JSON
        metadata = {
            'type': raster_type,
            'data_shape': raster.shape,
            'data_dtype': str(raster.dtype),
            'affine': list(vf.affine),
            'viewfinder_shape': vf.shape,
            'nodata': float(vf.nodata) if not np.isnan(vf.nodata) else 'nan',
            'crs': str(vf.crs),
            'mask_shape': vf.mask.shape,
            'mask_dtype': str(vf.mask.dtype),
            'metadata': raster.metadata
        }
        
        with open(f"{base_path}_raster.json", 'w') as f:
            json.dump(metadata, f, indent=2)
        
        # Save raster data as compressed numpy array
        np.savez_compressed(f"{base_path}_data.npz", data=np.asarray(raster))
        
        # Save mask as compressed numpy array
        np.savez_compressed(f"{base_path}_mask.npz", mask=vf.mask)
        
        print(f"{raster_type} saved to {base_path}.json, {base_path}_data.npz, and {base_path}_mask.npz")

    @staticmethod
    def load_raster(base_filename: Union[str, Path]) -> Union[Raster, MultiRaster]:
        """
        Load a Raster or MultiRaster object from JSON + NumPy format.
        
        Parameters
        ----------
        base_filename : str or Path
            Base filename (without extension)
            
        Returns
        -------
        Raster or MultiRaster
            The loaded raster object
        """
        base_path = Path(base_filename)
        
        # Load metadata
        with open(f"{base_path}_raster.json", 'r') as f:
            metadata = json.load(f)
        
        if metadata['type'] not in ['Raster', 'MultiRaster']:
            raise ValueError(f"Expected Raster or MultiRaster, got {metadata['type']}")
        
        # Load data and mask
        data_file = np.load(f"{base_path}_data.npz")
        mask_file = np.load(f"{base_path}_mask.npz")
        
        data = data_file['data']
        mask = mask_file['mask']
        
        # Handle NaN nodata values and ensure proper numpy type
        nodata = metadata['nodata']
        if nodata == 'nan':
            nodata = np.nan
        else:
            # Cast to numpy type that matches the data dtype
            data_dtype = np.dtype(metadata['data_dtype'])
            if np.issubdtype(data_dtype, np.floating):
                if data_dtype == np.float32:
                    nodata = np.float32(nodata)
                else:
                    nodata = np.float64(nodata)
            elif np.issubdtype(data_dtype, np.integer):
                if data_dtype == np.int16:
                    nodata = np.int16(nodata)
                elif data_dtype == np.int32:
                    nodata = np.int32(nodata)
                else:
                    nodata = np.int64(nodata)
            else:
                raise ValueError(f"Unsupported data dtype: {data_dtype}")
        
        # Reconstruct ViewFinder
        affine = Affine(*metadata['affine'])
        viewfinder = ViewFinder(
            affine=affine,
            shape=tuple(metadata['viewfinder_shape']),
            nodata=nodata,
            mask=mask,
            crs=projection.to_proj(metadata['crs'])
        )
        
        # Create appropriate raster type
        if metadata['type'] == 'MultiRaster':
            return MultiRaster(data, viewfinder, metadata['metadata'])
        else:
            return Raster(data, viewfinder, metadata['metadata'])

    @staticmethod
    def save_objects(objects: Dict[str, Any], base_filename: Union[str, Path]) -> None:
        """
        Save multiple pysheds objects to a single set of files.
        
        Parameters
        ----------
        objects : dict
            Dictionary of {name: object} to save
        base_filename : str or Path
            Base filename (without extension)
        """
        base_path = Path(base_filename)
        base_path.mkdir(parents=True, exist_ok=True)
        
        # Metadata for all objects
        all_metadata = {
            'objects': {},
            'saved_files': []
        }
        
        for name, obj in objects.items():
            if isinstance(obj, sGrid):
                PyshedsSerializer.save_sgrid(obj, f"{base_path}_{name}")
                all_metadata['objects'][name] = 'sGrid'
                all_metadata['saved_files'].extend([
                    f"{base_path}_{name}.json",
                    f"{base_path}_{name}_mask.npz"
                ])
            elif isinstance(obj, (Raster, MultiRaster)):
                PyshedsSerializer.save_raster(obj, f"{base_path}_{name}")
                raster_type = 'MultiRaster' if isinstance(obj, MultiRaster) else 'Raster'
                all_metadata['objects'][name] = raster_type
                all_metadata['saved_files'].extend([
                    f"{base_path}_{name}.json",
                    f"{base_path}_{name}_data.npz",
                    f"{base_path}_{name}_mask.npz"
                ])
            else:
                print(f"Warning: Object '{name}' of type {type(obj)} not supported")
        
        # Save index file
        with open(f"{base_path}_index.json", 'w') as f:
            json.dump(all_metadata, f, indent=2)
        
        print(f"Index saved to {base_path}_index.json")

    @staticmethod
    def load_objects(base_filename: Union[str, Path]) -> Dict[str, Any]:
        """
        Load multiple pysheds objects from a single set of files.
        
        Parameters
        ----------
        base_filename : str or Path
            Base filename (without extension)
            
        Returns
        -------
        dict
            Dictionary of {name: object}
        """
        base_path = Path(base_filename)
        
        # Load index
        with open(f"{base_path}_index.json", 'r') as f:
            index = json.load(f)
        
        objects = {}
        for name, obj_type in index['objects'].items():
            if obj_type == 'sGrid':
                objects[name] = PyshedsSerializer.load_sgrid(f"{base_path}_{name}")
            elif obj_type in ['Raster', 'MultiRaster']:
                objects[name] = PyshedsSerializer.load_raster(f"{base_path}_{name}")
        
        return objects


# Convenience functions
def save_sgrid(grid: sGrid, base_filename: Union[str, Path]) -> None:
    """Convenience function to save an sGrid."""
    PyshedsSerializer.save_sgrid(grid, base_filename)

def load_sgrid(base_filename: Union[str, Path]) -> sGrid:
    """Convenience function to load an sGrid."""
    return PyshedsSerializer.load_sgrid(base_filename)

def save_raster(raster: Union[Raster, MultiRaster], base_filename: Union[str, Path]) -> None:
    """Convenience function to save a Raster or MultiRaster."""
    PyshedsSerializer.save_raster(raster, base_filename)

def load_raster(base_filename: Union[str, Path]) -> Union[Raster, MultiRaster]:
    """Convenience function to load a Raster or MultiRaster."""
    return PyshedsSerializer.load_raster(base_filename)

def save_objects(objects: Dict[str, Any], base_filename: Union[str, Path]) -> None:
    """Convenience function to save multiple objects."""
    PyshedsSerializer.save_objects(objects, base_filename)

def load_objects(base_filename: Union[str, Path]) -> Dict[str, Any]:
    """Convenience function to load multiple objects."""
    return PyshedsSerializer.load_objects(base_filename)
