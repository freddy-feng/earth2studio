# SPDX-FileCopyrightText: Copyright (c) 2024 NVIDIA CORPORATION & AFFILIATES.
# SPDX-FileCopyrightText: All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from collections import OrderedDict

import numpy as np
import pytest

import earth2studio.run as run
from earth2studio.data import Random
from earth2studio.io import ZarrBackend
from earth2studio.models.px import Persistence
from earth2studio.perturbation import Gaussian, Zero


@pytest.mark.parametrize(
    "coords",
    [
        OrderedDict([("lat", np.arange(10)), ("lon", np.arange(20))]),
        OrderedDict([("c1", np.arange(5)), ("c2", np.arange(5)), ("c3", np.arange(5))]),
    ],
)
@pytest.mark.parametrize("variable", [["u10m", "v10m"], ["u10m", "u100", "nvidia"]])
@pytest.mark.parametrize("nsteps", [5, 10])
@pytest.mark.parametrize("nensemble", [1, 5, 10])
@pytest.mark.parametrize("batch_size", [None, 1, 11])
@pytest.mark.parametrize("perturbation_method", [Zero(), Gaussian()])
@pytest.mark.parametrize("time", [["2024-01-01"]])
@pytest.mark.parametrize("device", ["cpu", "cuda:0"])
def test_run_ensemble(
    coords, variable, nsteps, nensemble, batch_size, perturbation_method, time, device
):

    data = Random(domain_coords=coords)
    model = Persistence(variable, coords)

    io = ZarrBackend()

    io = run.ensemble(
        time,
        nsteps,
        nensemble,
        model,
        data,
        io,
        perturbation_method,
        batch_size=batch_size,
        device=device,
    )

    for var in variable:
        assert io[var].shape[0] == nensemble
        assert io[var].shape[1] == len(time)
        assert io[var].shape[2] == nsteps + 1
        for i, (key, value) in enumerate(coords.items()):
            assert io[var].shape[i + 3] == value.shape[0]

        assert not np.any(np.isnan(io[var][:]))
        assert not np.any(io[var][:] == 0.0)