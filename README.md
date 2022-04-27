<div id="top"></div>

<!-- PROJECT SHIELDS -->
<!--
*** I'm using markdown "reference style" links for readability.
*** Reference links are enclosed in brackets [ ] instead of parentheses ( ).
*** See the bottom of this document for the declaration of the reference variables
*** for contributors-url, forks-url, etc. This is an optional, concise syntax you may use.
*** https://www.markdownguide.org/basic-syntax/#reference-style-links
-->
[![Contributors][contributors-shield]][contributors-url]
[![Forks][forks-shield]][forks-url]
[![Stargazers][stars-shield]][stars-url]
[![Issues][issues-shield]][issues-url]
[![MIT License][license-shield]][license-url]
[![LinkedIn][linkedin-shield]][linkedin-url]



<!-- PROJECT LOGO -->
<br />
<div align="center">
  <a href="https://github.com/mabott/sghs">
    <img src="images/shotgrid_logo_wide.png" alt="Logo">
  </a>
  <a href="https://github.com/mabott/sghs">
    <img src="images/hs_logo.png" alt="Logo">
  </a>

<h3 align="center">Shotgrid Hammerspace</h3>

  <p align="center">
    a custom file metadata integration between Hammerspace and Shotgrid
    <br />
    <a href="https://github.com/mabott/sghs"><strong>Explore the docs »</strong></a>
    <br />
    <br />
    <a href="https://github.com/mabott/sghs">View Demo</a>
    ·
    <a href="https://github.com/mabott/sghs/issues">Report Bug</a>
    ·
    <a href="https://github.com/mabott/sghs/issues">Request Feature</a>
  </p>
</div>



<!-- TABLE OF CONTENTS -->
<details>
  <summary>Table of Contents</summary>
  <ol>
    <li>
      <a href="#about-the-project">About The Project</a>
      <ul>
        <li><a href="#built-with">Built With</a></li>
      </ul>
    </li>
    <li>
      <a href="#getting-started">Getting Started</a>
      <ul>
        <li><a href="#prerequisites">Prerequisites</a></li>
        <li><a href="#installation">Installation</a></li>
      </ul>
    </li>
    <li><a href="#usage">Usage</a></li>
    <li><a href="#roadmap">Roadmap</a></li>
    <li><a href="#contributing">Contributing</a></li>
    <li><a href="#license">License</a></li>
    <li><a href="#contact">Contact</a></li>
    <li><a href="#acknowledgments">Acknowledgments</a></li>
  </ol>
</details>



<!-- ABOUT THE PROJECT -->
## About The Project

Shothammer is a shotgunEvents plugin that can respond to status change events by setting
custom metadata on files and directories. This metadata can be used to drive data placement and location
using SmartObjectives on a Hammerspace Global Data Environment.

Currently, shothammer.py watches for tags added to or removed from shots in Shotgrid. When 
it sees tags in the allowed namespace (currently tags named `SGHS_*`) it adds them as
Hammerspace keywords to the root of the shot folder on disk. The tag schema is controlled in Shotgrid,
and they are passed through directly as keywords.

It finds the shot folder by using a per-project Pipeline Configuration fed to it by Shotgrid. This config can be specified
in Shotgrid by adding the plugin id `sghs.` to the specific pipeline configuration for the project.

Shothammer requests the template specified in `shothammer_config.ini` as `SGHS_PATH_TEMPLATE`.

sghs is intended to grow as a package over time with multiple plugin modules that do different things with Shotgrid's
events or webhooks.

<p align="right">(<a href="#top">back to top</a>)</p>

### Built With

* [Python](https://python.org/)
* [shotgunEvents](https://github.com/shotgunsoftware/shotgunEvents)
* [Shotgrid Toolkit](https://github.com/shotgunsoftware/tk-core)
* [Hammerspace Toolkit](https://github.com/hammer-space/hstk)

<p align="right">(<a href="#top">back to top</a>)</p>


<!-- GETTING STARTED -->
#Prerequisites


#Installation


#Configuration


#Troubleshooting


## Getting Started

Here are some basics on getting up and running. Everyone's Shotgrid instance is configured a bit differently and
will require some configuration depending on paths and pipeline configuration names and such.

### Prerequisites

1. Shotgrid API installed and configured 
2. Shotgrid event daemon installed and configured
3. Hammerspace Toolkit (hstk) installed: `$ pip install hstk`
4. Hammerspace file system mounted

### Installation

1. Clone this repository `git clone https://github.com/mabott/sghs.git`
2. Copy or hard link shothammer.py to your shotgunEvents plugin directory.

<p align="right">(<a href="#top">back to top</a>)</p>

### Configuration

1. Adjust shothammer_config.ini to fit environment (paths, fixing namespace overlap, etc.)
2. Copy shothammer_config.ini to shotgunEvents working directory 
3. One or more Hammerspace clusters set up with keyword-based objectives to drive data placement

### Troubleshooting
Given the appropriate values in shothammer_config.ini, the tests in test_shothammer.py should pass. If the plugin gets
disabled by shotgunEvents then there is a fatal problem somewhere. Running the tests using nose or your favorite IDE
should give enough details to show what is broken.

#### Things to check:
1. Make sure hstk is installed in the same environment running shotgunEvents.
2. Make sure the authentication information for Shotgrid is complete, both name and application key.



<!-- USAGE EXAMPLES -->
## Usage

Use this space to show useful examples of how a project can be used. Additional screenshots, code examples and demos work well in this space. You may also link to more resources.

_For more examples, please refer to the [Documentation](https://example.com)_

<p align="right">(<a href="#top">back to top</a>)</p>



<!-- ROADMAP -->
## Roadmap

- [ ] Reduce the weight of the recommended boilerplate pipeline config
- [ ] Find a path for more Shotgrid objects (currently just shots)
  - [ ] Sequences
  - [ ] Episodes
  - [ ] Specific assets


See the [open issues](https://github.com/mabott/sghs/issues) for a full list of proposed features (and known issues).

<p align="right">(<a href="#top">back to top</a>)</p>



<!-- CONTRIBUTING -->
## Contributing

We welcome contributions to this project so that we can make this plugin applicable to many different workflows!

If you have a suggestion that would improve this project, please fork the repo and create a pull request. You can also
simply open an issue with the tag "enhancement". Please don't forget to give the project a star! Thanks again!

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

<p align="right">(<a href="#top">back to top</a>)</p>



<!-- LICENSE -->
## License

Distributed under the MIT License. See `LICENSE` for more information.

<p align="right">(<a href="#top">back to top</a>)</p>



<!-- CONTACT -->
## Contact

Your Name - [@mabott](https://twitter.com/mabott) - mike.bott@hammerspace.com

Project Link: [https://github.com/mabott/sghs](https://github.com/mabott/sghs)

<p align="right">(<a href="#top">back to top</a>)</p>



<!-- ACKNOWLEDGMENTS -->
## Acknowledgments

This project wouldn't exist without these folks' contributions:

* [Jeremy Smith](mailto:jeremy.smith@jellyfishpictures.co.uk) of [Jellyfish Pictures](https://jellyfishpictures.co.uk/) 
for his technical vision, guidance, and support
* [Dan Hutchinson](dan.hutchinson@jellyfishpictures.co.uk) of [Jellyfish Pictures](https://jellyfishpictures.co.uk/)
for timely application of his Python and Shotgrid knowledge
* [Natasha Kelkar](natasha.kelkar@jellyfishpictures.co.uk) of [Jellyfish Pictures](https://jellyfishpictures.co.uk/)
for her technical direction-setting
* Our excellent crew at [Hammerspace](https://hammerspace.com/) for developing cool storage technology that solves 
interesting distributed storage problems

<p align="right">(<a href="#top">back to top</a>)</p>



<!-- MARKDOWN LINKS & IMAGES -->
<!-- https://www.markdownguide.org/basic-syntax/#reference-style-links -->
[contributors-shield]: https://img.shields.io/github/contributors/mabott/sghs.svg?style=for-the-badge
[contributors-url]: https://github.com/mabott/sghs/graphs/contributors
[forks-shield]: https://img.shields.io/github/forks/mabott/sghs.svg?style=for-the-badge
[forks-url]: https://github.com/mabott/sghs/network/members
[stars-shield]: https://img.shields.io/github/stars/mabott/sghs.svg?style=for-the-badge
[stars-url]: https://github.com/mabott/sghs/stargazers
[issues-shield]: https://img.shields.io/github/issues/mabott/sghs.svg?style=for-the-badge
[issues-url]: https://github.com/mabott/sghs/issues
[license-shield]: https://img.shields.io/github/license/mabott/sghs.svg?style=for-the-badge
[license-url]: https://github.com/mabott/sghs/blob/master/LICENSE.txt
[linkedin-shield]: https://img.shields.io/badge/-LinkedIn-black.svg?style=for-the-badge&logo=linkedin&colorB=555
[linkedin-url]: https://linkedin.com/in/mbott
[product-screenshot]: images/screenshot.png