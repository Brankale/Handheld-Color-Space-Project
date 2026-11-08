"""Read raw HCFR measurement blocks (document 3, measurements 17, Win32).

Derived from HCFR's CDataSetDoc, CMeasure, CColor and Matrix serialization.
This importable, read-only library preserves stored XYZ, spectra, lux,
settings and measurement ordering without correction or normalization.
It uses bounded binary reads, retains invalid records and sparse indices,
and skips legacy conversion matrices and trailing MFC session objects.
"""

# Original copyright notices:
# Copyright (c) 2005-2011 Association Homecinema Francophone. All rights reserved.
# Copyright (c) 2005-2007 Association Homecinema Francophone. All rights reserved.
# Original authors include Francois-Xavier CHABOUD and Georges GALLERAND;
# OS-independent reading code by Jerome Duquennoy.
#
# This file is subject to the terms of the GNU General Public License as
# published by the Free Software Foundation. The original distribution
# includes a copy in COPYING.htm; this port includes the complete text below.
# If you do not have a copy, you may obtain one by writing to the Free
# Software Foundation, 675 Mass Ave, Cambridge, MA 02139, USA.
#
# This software is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# Python port and changes: 2026-11-08. This port is distributed under GPL v2.
# Changes include measurements 17 support, bounded binary reads, preservation
# of invalid records and sparse indices, omission of legacy matrices and
# MFC session objects, and embedding the complete license in this file.
# Original notices specify GPL without a version-only restriction; choosing
# v2 here does not relicense the original HCFR sources.
#
# BEGIN GPL-2.0 LICENSE
#                     GNU GENERAL PUBLIC LICENSE
#                        Version 2, June 1991
#
#  Copyright (C) 1989, 1991 Free Software Foundation, Inc.,
#  <https://fsf.org/>
#  Everyone is permitted to copy and distribute verbatim copies
#  of this license document, but changing it is not allowed.
#
#                             Preamble
#
#   The licenses for most software are designed to take away your
# freedom to share and change it.  By contrast, the GNU General Public
# License is intended to guarantee your freedom to share and change free
# software--to make sure the software is free for all its users.  This
# General Public License applies to most of the Free Software
# Foundation's software and to any other program whose authors commit to
# using it.  (Some other Free Software Foundation software is covered by
# the GNU Lesser General Public License instead.)  You can apply it to
# your programs, too.
#
#   When we speak of free software, we are referring to freedom, not
# price.  Our General Public Licenses are designed to make sure that you
# have the freedom to distribute copies of free software (and charge for
# this service if you wish), that you receive source code or can get it
# if you want it, that you can change the software or use pieces of it
# in new free programs; and that you know you can do these things.
#
#   To protect your rights, we need to make restrictions that forbid
# anyone to deny you these rights or to ask you to surrender the rights.
# These restrictions translate to certain responsibilities for you if you
# distribute copies of the software, or if you modify it.
#
#   For example, if you distribute copies of such a program, whether
# gratis or for a fee, you must give the recipients all the rights that
# you have.  You must make sure that they, too, receive or can get the
# source code.  And you must show them these terms so they know their
# rights.
#
#   We protect your rights with two steps: (1) copyright the software, and
# (2) offer you this license which gives you legal permission to copy,
# distribute and/or modify the software.
#
#   Also, for each author's protection and ours, we want to make certain
# that everyone understands that there is no warranty for this free
# software.  If the software is modified by someone else and passed on, we
# want its recipients to know that what they have is not the original, so
# that any problems introduced by others will not reflect on the original
# authors' reputations.
#
#   Finally, any free program is threatened constantly by software
# patents.  We wish to avoid the danger that redistributors of a free
# program will individually obtain patent licenses, in effect making the
# program proprietary.  To prevent this, we have made it clear that any
# patent must be licensed for everyone's free use or not licensed at all.
#
#   The precise terms and conditions for copying, distribution and
# modification follow.
#
#                     GNU GENERAL PUBLIC LICENSE
#    TERMS AND CONDITIONS FOR COPYING, DISTRIBUTION AND MODIFICATION
#
#   0. This License applies to any program or other work which contains
# a notice placed by the copyright holder saying it may be distributed
# under the terms of this General Public License.  The "Program", below,
# refers to any such program or work, and a "work based on the Program"
# means either the Program or any derivative work under copyright law:
# that is to say, a work containing the Program or a portion of it,
# either verbatim or with modifications and/or translated into another
# language.  (Hereinafter, translation is included without limitation in
# the term "modification".)  Each licensee is addressed as "you".
#
# Activities other than copying, distribution and modification are not
# covered by this License; they are outside its scope.  The act of
# running the Program is not restricted, and the output from the Program
# is covered only if its contents constitute a work based on the
# Program (independent of having been made by running the Program).
# Whether that is true depends on what the Program does.
#
#   1. You may copy and distribute verbatim copies of the Program's
# source code as you receive it, in any medium, provided that you
# conspicuously and appropriately publish on each copy an appropriate
# copyright notice and disclaimer of warranty; keep intact all the
# notices that refer to this License and to the absence of any warranty;
# and give any other recipients of the Program a copy of this License
# along with the Program.
#
# You may charge a fee for the physical act of transferring a copy, and
# you may at your option offer warranty protection in exchange for a fee.
#
#   2. You may modify your copy or copies of the Program or any portion
# of it, thus forming a work based on the Program, and copy and
# distribute such modifications or work under the terms of Section 1
# above, provided that you also meet all of these conditions:
#
#     a) You must cause the modified files to carry prominent notices
#     stating that you changed the files and the date of any change.
#
#     b) You must cause any work that you distribute or publish, that in
#     whole or in part contains or is derived from the Program or any
#     part thereof, to be licensed as a whole at no charge to all third
#     parties under the terms of this License.
#
#     c) If the modified program normally reads commands interactively
#     when run, you must cause it, when started running for such
#     interactive use in the most ordinary way, to print or display an
#     announcement including an appropriate copyright notice and a
#     notice that there is no warranty (or else, saying that you provide
#     a warranty) and that users may redistribute the program under
#     these conditions, and telling the user how to view a copy of this
#     License.  (Exception: if the Program itself is interactive but
#     does not normally print such an announcement, your work based on
#     the Program is not required to print an announcement.)
#
# These requirements apply to the modified work as a whole.  If
# identifiable sections of that work are not derived from the Program,
# and can be reasonably considered independent and separate works in
# themselves, then this License, and its terms, do not apply to those
# sections when you distribute them as separate works.  But when you
# distribute the same sections as part of a whole which is a work based
# on the Program, the distribution of the whole must be on the terms of
# this License, whose permissions for other licensees extend to the
# entire whole, and thus to each and every part regardless of who wrote it.
#
# Thus, it is not the intent of this section to claim rights or contest
# your rights to work written entirely by you; rather, the intent is to
# exercise the right to control the distribution of derivative or
# collective works based on the Program.
#
# In addition, mere aggregation of another work not based on the Program
# with the Program (or with a work based on the Program) on a volume of
# a storage or distribution medium does not bring the other work under
# the scope of this License.
#
#   3. You may copy and distribute the Program (or a work based on it,
# under Section 2) in object code or executable form under the terms of
# Sections 1 and 2 above provided that you also do one of the following:
#
#     a) Accompany it with the complete corresponding machine-readable
#     source code, which must be distributed under the terms of Sections
#     1 and 2 above on a medium customarily used for software interchange; or,
#
#     b) Accompany it with a written offer, valid for at least three
#     years, to give any third party, for a charge no more than your
#     cost of physically performing source distribution, a complete
#     machine-readable copy of the corresponding source code, to be
#     distributed under the terms of Sections 1 and 2 above on a medium
#     customarily used for software interchange; or,
#
#     c) Accompany it with the information you received as to the offer
#     to distribute corresponding source code.  (This alternative is
#     allowed only for noncommercial distribution and only if you
#     received the program in object code or executable form with such
#     an offer, in accord with Subsection b above.)
#
# The source code for a work means the preferred form of the work for
# making modifications to it.  For an executable work, complete source
# code means all the source code for all modules it contains, plus any
# associated interface definition files, plus the scripts used to
# control compilation and installation of the executable.  However, as a
# special exception, the source code distributed need not include
# anything that is normally distributed (in either source or binary
# form) with the major components (compiler, kernel, and so on) of the
# operating system on which the executable runs, unless that component
# itself accompanies the executable.
#
# If distribution of executable or object code is made by offering
# access to copy from a designated place, then offering equivalent
# access to copy the source code from the same place counts as
# distribution of the source code, even though third parties are not
# compelled to copy the source along with the object code.
#
#   4. You may not copy, modify, sublicense, or distribute the Program
# except as expressly provided under this License.  Any attempt
# otherwise to copy, modify, sublicense or distribute the Program is
# void, and will automatically terminate your rights under this License.
# However, parties who have received copies, or rights, from you under
# this License will not have their licenses terminated so long as such
# parties remain in full compliance.
#
#   5. You are not required to accept this License, since you have not
# signed it.  However, nothing else grants you permission to modify or
# distribute the Program or its derivative works.  These actions are
# prohibited by law if you do not accept this License.  Therefore, by
# modifying or distributing the Program (or any work based on the
# Program), you indicate your acceptance of this License to do so, and
# all its terms and conditions for copying, distributing or modifying
# the Program or works based on it.
#
#   6. Each time you redistribute the Program (or any work based on the
# Program), the recipient automatically receives a license from the
# original licensor to copy, distribute or modify the Program subject to
# these terms and conditions.  You may not impose any further
# restrictions on the recipients' exercise of the rights granted herein.
# You are not responsible for enforcing compliance by third parties to
# this License.
#
#   7. If, as a consequence of a court judgment or allegation of patent
# infringement or for any other reason (not limited to patent issues),
# conditions are imposed on you (whether by court order, agreement or
# otherwise) that contradict the conditions of this License, they do not
# excuse you from the conditions of this License.  If you cannot
# distribute so as to satisfy simultaneously your obligations under this
# License and any other pertinent obligations, then as a consequence you
# may not distribute the Program at all.  For example, if a patent
# license would not permit royalty-free redistribution of the Program by
# all those who receive copies directly or indirectly through you, then
# the only way you could satisfy both it and this License would be to
# refrain entirely from distribution of the Program.
#
# If any portion of this section is held invalid or unenforceable under
# any particular circumstance, the balance of the section is intended to
# apply and the section as a whole is intended to apply in other
# circumstances.
#
# It is not the purpose of this section to induce you to infringe any
# patents or other property right claims or to contest validity of any
# such claims; this section has the sole purpose of protecting the
# integrity of the free software distribution system, which is
# implemented by public license practices.  Many people have made
# generous contributions to the wide range of software distributed
# through that system in reliance on consistent application of that
# system; it is up to the author/donor to decide if he or she is willing
# to distribute software through any other system and a licensee cannot
# impose that choice.
#
# This section is intended to make thoroughly clear what is believed to
# be a consequence of the rest of this License.
#
#   8. If the distribution and/or use of the Program is restricted in
# certain countries either by patents or by copyrighted interfaces, the
# original copyright holder who places the Program under this License
# may add an explicit geographical distribution limitation excluding
# those countries, so that distribution is permitted only in or among
# countries not thus excluded.  In such case, this License incorporates
# the limitation as if written in the body of this License.
#
#   9. The Free Software Foundation may publish revised and/or new versions
# of the General Public License from time to time.  Such new versions will
# be similar in spirit to the present version, but may differ in detail to
# address new problems or concerns.
#
# Each version is given a distinguishing version number.  If the Program
# specifies a version number of this License which applies to it and "any
# later version", you have the option of following the terms and conditions
# either of that version or of any later version published by the Free
# Software Foundation.  If the Program does not specify a version number of
# this License, you may choose any version ever published by the Free Software
# Foundation.
#
#   10. If you wish to incorporate parts of the Program into other free
# programs whose distribution conditions are different, write to the author
# to ask for permission.  For software which is copyrighted by the Free
# Software Foundation, write to the Free Software Foundation; we sometimes
# make exceptions for this.  Our decision will be guided by the two goals
# of preserving the free status of all derivatives of our free software and
# of promoting the sharing and reuse of software generally.
#
#                             NO WARRANTY
#
#   11. BECAUSE THE PROGRAM IS LICENSED FREE OF CHARGE, THERE IS NO WARRANTY
# FOR THE PROGRAM, TO THE EXTENT PERMITTED BY APPLICABLE LAW.  EXCEPT WHEN
# OTHERWISE STATED IN WRITING THE COPYRIGHT HOLDERS AND/OR OTHER PARTIES
# PROVIDE THE PROGRAM "AS IS" WITHOUT WARRANTY OF ANY KIND, EITHER EXPRESSED
# OR IMPLIED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE.  THE ENTIRE RISK AS
# TO THE QUALITY AND PERFORMANCE OF THE PROGRAM IS WITH YOU.  SHOULD THE
# PROGRAM PROVE DEFECTIVE, YOU ASSUME THE COST OF ALL NECESSARY SERVICING,
# REPAIR OR CORRECTION.
#
#   12. IN NO EVENT UNLESS REQUIRED BY APPLICABLE LAW OR AGREED TO IN WRITING
# WILL ANY COPYRIGHT HOLDER, OR ANY OTHER PARTY WHO MAY MODIFY AND/OR
# REDISTRIBUTE THE PROGRAM AS PERMITTED ABOVE, BE LIABLE TO YOU FOR DAMAGES,
# INCLUDING ANY GENERAL, SPECIAL, INCIDENTAL OR CONSEQUENTIAL DAMAGES ARISING
# OUT OF THE USE OR INABILITY TO USE THE PROGRAM (INCLUDING BUT NOT LIMITED
# TO LOSS OF DATA OR DATA BEING RENDERED INACCURATE OR LOSSES SUSTAINED BY
# YOU OR THIRD PARTIES OR A FAILURE OF THE PROGRAM TO OPERATE WITH ANY OTHER
# PROGRAMS), EVEN IF SUCH HOLDER OR OTHER PARTY HAS BEEN ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGES.
#
#                      END OF TERMS AND CONDITIONS
#
#             How to Apply These Terms to Your New Programs
#
#   If you develop a new program, and you want it to be of the greatest
# possible use to the public, the best way to achieve this is to make it
# free software which everyone can redistribute and change under these terms.
#
#   To do so, attach the following notices to the program.  It is safest
# to attach them to the start of each source file to most effectively
# convey the exclusion of warranty; and each file should have at least
# the "copyright" line and a pointer to where the full notice is found.
#
#     <one line to give the program's name and a brief idea of what it does.>
#     Copyright (C) <year>  <name of author>
#
#     This program is free software; you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation; either version 2 of the License, or
#     (at your option) any later version.
#
#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License along
#     with this program; if not, see <https://www.gnu.org/licenses/>.
#
# Also add information on how to contact you by electronic and paper mail.
#
# If the program is interactive, make it output a short notice like this
# when it starts in an interactive mode:
#
#     Gnomovision version 69, Copyright (C) year name of author
#     Gnomovision comes with ABSOLUTELY NO WARRANTY; for details type `show w'.
#     This is free software, and you are welcome to redistribute it
#     under certain conditions; type `show c' for details.
#
# The hypothetical commands `show w' and `show c' should show the appropriate
# parts of the General Public License.  Of course, the commands you use may
# be called something other than `show w' and `show c'; they could even be
# mouse-clicks or menu items--whatever suits your program.
#
# You should also get your employer (if you work as a programmer) or your
# school, if any, to sign a "copyright disclaimer" for the program, if
# necessary.  Here is a sample; alter the names:
#
#   Yoyodyne, Inc., hereby disclaims all copyright interest in the program
#   `Gnomovision' (which makes passes at compilers) written by James Hacker.
#
#   <signature of Moe Ghoul>, 1 April 1989
#   Moe Ghoul, President of Vice
#
# This General Public License does not permit incorporating your program into
# proprietary programs.  If your program is a subroutine library, you may
# consider it more useful to permit linking proprietary applications with the
# library.  If this is what you want to do, use the GNU Lesser General
# Public License instead of this License.
# END GPL-2.0 LICENSE

from dataclasses import dataclass
import codecs
from os import PathLike
from pathlib import Path
import struct
from types import MappingProxyType
from typing import BinaryIO, Mapping


__all__ = [
    "ChcMeasurements", "ChcParseError", "ColorMeasurement", "Limits",
    "RawString", "Spectrum", "UnsupportedVersionError", "read_chc",
]


class ChcParseError(ValueError):
    """Malformed or truncated data, with a document-relative byte offset."""

    def __init__(self, message: str, offset: int, context: str):
        self.offset = offset
        self.context = context
        super().__init__(f"{context} at byte {offset}: {message}")


class UnsupportedVersionError(ChcParseError):
    """A serialization version outside the supported layout."""


@dataclass(frozen=True)
class Limits:
    """Resource limits across one document, including skipped payloads.

    Bound cumulative color records, declared array slots, matrix dimensions
    and element counts, note bytes, and total bytes consumed. Defaults are
    100,000 colors, 100,000 slots, 1,000,000 matrix elements, 8 MiB of note
    bytes, and 256 MiB consumed per document. These are safety bounds, not
    measurement corrections. Pass explicit limits to read_chc
    for trusted larger documents.
    """

    max_colors: int = 100_000
    max_slots: int = 100_000
    max_matrix_elements: int = 1_000_000
    max_text_bytes: int = 8 * 1024 * 1024
    max_total_bytes: int = 256 * 1024 * 1024

    def __post_init__(self):
        for name, value in vars(self).items():
            if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
                raise ValueError(f"{name} must be a positive integer")


@dataclass(frozen=True)
class RawString:
    """Original CString bytes; multibyte text has no stored code page."""

    data: bytes
    is_unicode: bool

    def decode(self, encoding: str | None = None) -> str:
        if self.is_unicode:
            if encoding is not None and codecs.lookup(encoding).name != "utf-16-le":
                raise ValueError("Unicode CString uses UTF-16LE")
            return self.data.decode("utf-16le", errors="strict")
        if encoding is None:
            raise ValueError("multibyte CString requires an explicit encoding")
        return self.data.decode(encoding, errors="strict")


@dataclass(frozen=True)
class Spectrum:
    """Stored spectral grid metadata and unmodified samples."""

    version: int
    band_count: int
    wavelength_min: int
    wavelength_max: int
    bandwidth: int | float
    samples: tuple[float, ...]
    samples_offset: int


@dataclass(frozen=True)
class ColorMeasurement:
    """One serialized record; invalid XYZ are preserved, not filtered."""

    version: int
    xyz: tuple[float, float, float]
    spectrum: Spectrum | None
    lux: float | None
    file_offset: int

    @property
    def is_valid(self) -> bool:
        """HCFR validity criterion, without changing the stored values."""
        return all(component > -1.0 for component in self.xyz)


@dataclass(frozen=True)
class ChcMeasurements:
    """Raw measurement block; trailing MFC session objects are not parsed."""

    document_version: int
    measurement_version: int
    settings: Mapping[str, int | float]
    user_black: ColorMeasurement
    grayscale: tuple[ColorMeasurement, ...]
    near_black: tuple[ColorMeasurement, ...]
    near_white: tuple[ColorMeasurement, ...]
    saturations: Mapping[str, tuple[ColorMeasurement, ...]]
    color_checker: tuple[ColorMeasurement | None, ...]
    color_checker_master: tuple[ColorMeasurement | None, ...]
    free_measurements: tuple[ColorMeasurement, ...]
    primaries: Mapping[str, ColorMeasurement]
    secondaries: Mapping[str, ColorMeasurement]
    on_off_black: ColorMeasurement
    on_off_white: ColorMeasurement
    ansi_black: ColorMeasurement
    ansi_white: ColorMeasurement
    prime_white: ColorMeasurement
    notes: RawString
    ire_scale_mode: int
    measurements_end_offset: int


_SETTINGS_LAYOUT = (
    ("bt2390_bs", "d"), ("bt2390_ws", "d"), ("bt2390_ws1", "d"),
    ("target_system_gamma", "d"),
    ("master_min_luminance", "d"), ("master_max_luminance", "d"),
    ("target_min_luminance", "d"), ("target_max_luminance", "d"),
    ("content_max_luminance", "d"), ("frame_average_max_luminance", "d"),
    ("use_tone_map", "i"), ("override_targets", "i"),
    ("diffuse_luminance", "d"), ("near_white_clip_color", "I"),
    ("white_target", "i"), ("color_checker_mode", "i"),
    ("color_standard", "i"), ("delta_e_formula", "i"),
    ("delta_e_gray", "i"), ("gray_world_weight", "i"),
    ("gamma_offset_type", "i"), ("gamma_reference", "d"),
    ("gamma_relative", "d"), ("split", "d"),
    ("manual_white_x", "d"), ("manual_white_y", "d"),
    ("use_measured_gamma", "i"),
    ("manual_blue_x", "d"), ("manual_red_x", "d"),
    ("manual_green_x", "d"), ("manual_blue_y", "d"),
    ("manual_red_y", "d"), ("manual_green_y", "d"),
    ("override_black", "i"),
)
_MARKER = (0.123, 0.456, 0.789)


class _Reader:
    def __init__(self, stream: BinaryIO, limits: Limits):
        self.stream = stream
        self.limits = limits
        self.offset = 0
        self.colors = 0
        self.slots = 0

    def fail(self, message: str, context: str):
        raise ChcParseError(message, self.offset, context)

    def exact(self, size: int, context: str) -> bytes:
        if size < 0 or self.offset + size > self.limits.max_total_bytes:
            self.fail("document byte limit exceeded", context)
        chunks = []
        remaining = size
        while remaining:
            chunk = self.stream.read(min(remaining, 65536))
            if not isinstance(chunk, bytes):
                raise TypeError("_load_chc requires a binary stream returning bytes")
            if not chunk:
                self.fail(f"truncated data ({remaining} bytes missing)", context)
            if len(chunk) > remaining:
                self.fail("stream returned more bytes than requested", context)
            chunks.append(chunk)
            remaining -= len(chunk)
            self.offset += len(chunk)
        return b"".join(chunks)

    def scalar(self, format_code: str, context: str):
        format_string = "<" + format_code
        return struct.unpack(
            format_string, self.exact(struct.calcsize(format_string), context)
        )[0]

    def version(self, supported: tuple[int, ...], context: str) -> int:
        offset = self.offset
        version = self.scalar("i", context)
        if version not in supported:
            raise UnsupportedVersionError(f"unsupported version {version}", offset, context)
        return version

    def count(self, context: str) -> int:
        count = self.scalar("i", context)
        if count < 0 or self.slots + count > self.limits.max_slots:
            self.fail("invalid count or total slot limit exceeded", context)
        self.slots += count
        return count

    def matrix(
        self, context: str, expected: tuple[int, int] | None = None,
        skip: bool = False,
    ):
        """Read or skip the layout of Matrix::Serialize in libHCFR/matrix.cpp."""
        if self.exact(8, context) != struct.pack("<II", 0x434D6174, 0x72697843):
            self.fail("invalid matrix signature", context)
        self.version((1,), context + ".version")
        columns = self.scalar("i", context + ".columns")
        rows = self.scalar("i", context + ".rows")
        elements = columns * rows
        if min(columns, rows) < 0 or max(columns, rows, elements) > self.limits.max_matrix_elements:
            self.fail("invalid dimensions or matrix limit exceeded", context)
        if expected is not None and (columns, rows) != expected:
            self.fail(f"expected columns/rows {expected}, got {(columns, rows)}", context)
        size = elements * 8
        if skip:
            while size:
                chunk_size = min(size, 65536)
                self.exact(chunk_size, context + ".data")
                size -= chunk_size
            return None
        return struct.unpack(f"<{elements}d", self.exact(size, context + ".data"))

    def color(self, context: str) -> ColorMeasurement:
        """Read CColor::Serialize and CSpectrum::Serialize from libHCFR/Color.cpp.

        Preserve stored XYZ, spectral samples and lux without applying the
        two legacy conversion matrices serialized within each color record.
        These matrices are structurally checked and skipped, not exposed.
        """
        offset = self.offset
        self.colors += 1
        if self.colors > self.limits.max_colors:
            self.fail("color record limit exceeded", context)
        version = self.version((1, 2, 3, 4, 5, 6), context + ".version")
        xyz = self.matrix(context + ".xyz", expected=(1, 3))
        self.matrix(context + ".legacy_xyz_to_sensor", skip=True)
        self.matrix(context + ".legacy_sensor_to_xyz", skip=True)
        spectrum = None
        if version in (2, 4, 5, 6):
            bands = self.scalar("i", context + ".spectrum.band_count")
            if bands < 0 or bands > self.limits.max_matrix_elements:
                self.fail("invalid spectral band count", context)
            minimum = self.scalar("i", context + ".spectrum.wavelength_min")
            maximum = self.scalar("i", context + ".spectrum.wavelength_max")
            bandwidth = self.scalar(
                "i" if version in (2, 4) else "d", context + ".spectrum.bandwidth"
            )
            spectrum_version = self.version((1,), context + ".spectrum.version")
            samples_offset = self.offset + 20
            samples = self.matrix(context + ".spectrum.samples", expected=(1, bands))
            spectrum = Spectrum(
                spectrum_version, bands, minimum, maximum, bandwidth,
                samples, samples_offset,
            )
        lux = self.scalar("d", context + ".lux") if version in (3, 4, 6) else None
        return ColorMeasurement(version, xyz, spectrum, lux, offset)

    def array(self, context: str) -> tuple[ColorMeasurement, ...]:
        count = self.count(context + ".count")
        return tuple(self.color(f"{context}[{index}]") for index in range(count))

    def sparse(self, context: str) -> tuple[ColorMeasurement | None, ...]:
        """Read indexed ColorChecker records from CMeasure::Serialize (Measure.cpp).

        Consume the terminating color marker even for empty or full arrays;
        preserve absent slots as None rather than synthesizing measurements.
        A genuine measurement with the marker XYZ (0.123, 0.456, 0.789) is
        ambiguous in HCFR's format, which provides no escape mechanism.
        Missing markers and duplicate or out-of-range indices raise
        ChcParseError with the document-relative offset and parsing context.
        """
        count = self.count(context + ".count")
        slots = [None] * count
        for record in range(count + 1):
            color = self.color(f"{context}.record[{record}]")
            if color.xyz == _MARKER:
                return tuple(slots)
            if record == count:
                self.fail("missing ColorChecker end marker", context)
            index = self.scalar("i", context + ".index")
            if not 0 <= index < count:
                self.fail(f"index {index} outside declared size {count}", context)
            if slots[index] is not None:
                self.fail(f"duplicate index {index}", context)
            slots[index] = color
        raise AssertionError("unreachable")

    def string(self, context: str) -> RawString:
        length = self.scalar("B", context + ".length")
        unicode = False
        if length == 0xFF:
            length = self.scalar("H", context + ".length")
            if length == 0xFFFE:
                unicode = True
                length = self.scalar("B", context + ".length")
                if length == 0xFF:
                    length = self.scalar("H", context + ".length")
                    if length == 0xFFFE:
                        self.fail("repeated Unicode string marker", context)
            if length == 0xFFFF:
                length = self.scalar("I", context + ".length")
                if length == 0xFFFFFFFF:
                    length = self.scalar("Q", context + ".length")
        size = length * (2 if unicode else 1)
        if size > self.limits.max_text_bytes:
            self.fail("text byte limit exceeded", context)
        return RawString(self.exact(size, context + ".data"), unicode)


def _load_chc(stream: BinaryIO, *, limits: Limits | None = None) -> ChcMeasurements:
    """Read from the stream's current position, stopping before MFC objects.

    Offsets are relative to that position. The stream need not be seekable
    and is not closed. No color values or settings are transformed.

    Sensor/generator objects, window layout, hardware access, and the
    remainder of the MFC session are not parsed or validated. The returned
    measurements_end_offset is relative to the starting position; the
    stream remains immediately after the measurement block at that offset.

    Invalid structures, truncated data and exceeded resource limits raise
    ChcParseError with offset and context. Unsupported versions raise its
    subclass UnsupportedVersionError. Stream I/O errors propagate unchanged.
    The limits argument defaults to Limits(); see it for resource bounds.

    The document header follows HCFR's CDataSetDoc::Serialize in
    datasetdoc.cpp. Settings and measurement ordering follow
    CMeasure::Serialize in Measure.cpp, without its application-level
    black/white fallback substitutions or trailing sensor/generator objects.
    """
    reader = _Reader(stream, limits if limits is not None else Limits())
    if reader.exact(8, "document.signature") != b"COLORHCF":
        reader.fail("invalid CHC signature", "document.signature")
    document_version = reader.version((3,), "document.version")
    measurement_version = reader.version((17,), "measurements.version")
    settings = MappingProxyType({
        name: reader.scalar(code, "settings." + name)
        for name, code in _SETTINGS_LAYOUT
    })
    user_black = reader.color("user_black")
    grayscale = reader.array("grayscale")
    near_black = reader.array("near_black")
    near_white = reader.array("near_white")
    saturations = MappingProxyType({
        name: reader.array("saturations." + name)
        for name in ("R", "G", "B", "Y", "C", "M")
    })
    color_checker = reader.sparse("color_checker")
    color_checker_master = reader.sparse("color_checker_master")
    free_measurements = reader.array("free_measurements")
    primaries = MappingProxyType({
        name: reader.color("primaries." + name) for name in ("R", "G", "B")
    })
    secondaries = MappingProxyType({
        name: reader.color("secondaries." + name) for name in ("Y", "C", "M")
    })
    on_off_black = reader.color("on_off_black")
    on_off_white = reader.color("on_off_white")
    ansi_black = reader.color("ansi_black")
    ansi_white = reader.color("ansi_white")
    prime_white = reader.color("prime_white")
    notes = reader.string("notes")
    ire_scale_mode = reader.scalar("i", "ire_scale_mode")
    return ChcMeasurements(
        document_version, measurement_version, settings, user_black,
        grayscale, near_black, near_white, saturations, color_checker,
        color_checker_master, free_measurements, primaries, secondaries,
        on_off_black, on_off_white, ansi_black, ansi_white, prime_white,
        notes, ire_scale_mode, reader.offset,
    )


def read_chc(path: str | PathLike[str], *, limits: Limits | None = None) -> ChcMeasurements:
    """Open a CHC file in binary mode and return its raw measurement block.

    Close the file after reading, including on failure. Parsing exclusions,
    resource limits and parse errors are documented in _load_chc and Limits.
    Filesystem errors propagate as OSError subclasses.
    """
    with Path(path).open("rb") as stream:
        return _load_chc(stream, limits=limits)